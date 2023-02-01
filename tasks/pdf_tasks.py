import fitz
from cloud.minio_utils import config, minio_client
import io
from tasks.worker import *
from database.models import *
from app import celery_pdf_process
import base64
import requests
import traceback
import json
from .utils.pdf_utils import * 

APP_HOST = 'http://localhost:3500'

# Đọc PDF (Lấy pdf và chuyển dưới dạng base64 string)
@celery_pdf_process.task()
def get_pdf(pdf_object_key):
    response = minio_client.get_object(config["BASE_BUCKET"], pdf_object_key)
    doc = fitz.open("pdf", response.data)
    doc_bytes = doc.tobytes()
    base64_doc_bytes = base64.b64encode(doc_bytes)
    return base64_doc_bytes.decode('ascii')

# Tạo câu và bounding box cho trang
@celery_pdf_process.task()
def bounding_box_preprocess(doc_message, page_id):
    try:
        doc = convert_base64_to_pdf(doc_message)
        page = doc[0]
        sentences = read_page(page)
        idx = 1 # Biến đếm index câu
        for wordList in sentences:
            if (len(wordList)==0):# Tồn tại những word list rỗng (Không rõ lý do)
                continue
            # Tạo sentence object và lưu vào csdl
            text = get_text(wordList)
            boundingBoxList = []
            startPoints, endPoints = merge_bounding_box(wordList)        
            for (startPoint, endPoint) in zip(startPoints, endPoints):
                boundingBoxList.append(convert_bb_type(startPoint, endPoint))
            create_response = requests.post(f"{APP_HOST}/api/sentences", data={"index": idx, "text": text, "boundingBox": json.dumps(boundingBoxList), "pageId": page_id})
            idx+=1

        # Update trạng thái trang
        update_status_response = requests.put(f"{APP_HOST}/api/pages/{page_id}", data = {"pdfStatus": Status.READY, "audioStatus": Status.PROCESSING})
        return update_status_response.status_code
    except Exception as e:
        print('bb preprocess task', e)
        requests.put(f"{APP_HOST}/api/pages/{page_id}", data = {"pdfStatus": Status.ERROR})

# Chuyển pdf thành ảnh
@celery_pdf_process.task()
def convert_pdf_to_image(doc_message, page_id, image_status, page_img_object_key):
    if image_status == Status.NEW:
        try:
            doc = convert_base64_to_pdf(doc_message)
            pix = doc[0].get_pixmap()
            data = pix.pil_tobytes(format="png", optimize=True)
            raw_img = io.BytesIO(data)
            raw_img_size = raw_img.getbuffer().nbytes
            minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                    object_name = page_img_object_key, 
                                    data = raw_img, 
                                    length= raw_img_size,
                                    content_type = 'image/png')
            update_response = requests.put(f"{APP_HOST}/api/pages/{page_id}", data = {"imageStatus": Status.READY})
            return update_response.status_code
        except Exception as e:
            requests.put(f"{APP_HOST}/api/pages/{page_id}", data = {"imageStatus": Status.ERROR})
    elif image_status == Status.PROCESSING:
        return 'image is already completed'

# Chia pdf sách ra thành các trang
@celery_pdf_process.task()
def split_book_page(doc_message, from_page, to_page, chapter_id):
    try:
        doc = convert_base64_to_pdf(doc_message)
        for (idx, i) in enumerate(range(from_page-1, to_page)):
            # Tạo Page và lưu vào db
            page_write_response = requests.post(f"{APP_HOST}/api/pages", data={'index': idx+1, 'chapterId': chapter_id, 'ocrStatus': Status.READY, 'imageStatus': Status.READY})
            page_id = page_write_response.json()['pageId']
            # Lấy object key của image và pdf
            object_key_response = requests.post(f"{APP_HOST}/api/object_keys", data={'type': 'page', 'id': page_id})
            object_key = object_key_response.json()

            # Load PDF page
            page_doc = fitz.open() # an empty pdf file is opened
            page_doc.insert_pdf(doc, from_page=i, to_page=i)

            # Resize PDF to A4
            resize_doc = fitz.open()  # new empty PDF
            page = resize_doc.new_page()  # new page in A4 format
            page.show_pdf_page(page.rect, page_doc, 0)

            # Upload ảnh lên Cloud
            pix = resize_doc[0].get_pixmap()
            img_data = pix.pil_tobytes(format="png", optimize=True)
            raw_img = io.BytesIO(img_data)
            raw_img_size = raw_img.getbuffer().nbytes
            minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                    object_name = object_key['image-path'], 
                                    data = raw_img, 
                                    length= raw_img_size,
                                    content_type = 'image/png')

            # Upload PDF lên Cloud
            pdf_data = resize_doc.tobytes()
            raw_pdf = io.BytesIO(pdf_data)
            raw_pdf_size = raw_pdf.getbuffer().nbytes
            minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                    object_name = object_key['pdf-path'], 
                                    data = raw_pdf, 
                                    length= raw_pdf_size,
                                    content_type = 'application/pdf')
            
            page_preprocess_response = requests.post(f"{APP_HOST}/api/preprocess/page", data={'pageId': page_id})
    except Exception as e:
        print('split book', e)
        return "error"

# Thêm trang mới vào chapter (được lấy từ pdf)
@celery_pdf_process.task()
def add_new_page(doc_message, idx, page_id): 
    try:
        doc = convert_base64_to_pdf(doc_message)
        # Lấy object key của image và pdf
        object_key_response = requests.post(f"{APP_HOST}/api/object_keys", data={'type': 'page', 'id': page_id})
        object_key = object_key_response.json()

        # Load PDF page
        page_doc = fitz.open() # an empty pdf file is opened
        page_doc.insert_pdf(doc, from_page=idx-1, to_page=idx-1)

        # Resize PDF to A4
        resize_doc = fitz.open()  # new empty PDF
        page = resize_doc.new_page()  # new page in A4 format
        page.show_pdf_page(page.rect, page_doc, 0)

        # Upload ảnh lên Cloud
        pix = resize_doc[0].get_pixmap()
        img_data = pix.pil_tobytes(format="png", optimize=True)
        raw_img = io.BytesIO(img_data)
        raw_img_size = raw_img.getbuffer().nbytes
        minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                object_name = object_key['image-path'], 
                                data = raw_img, 
                                length= raw_img_size,
                                content_type = 'image/png')

        # Upload PDF lên Cloud
        pdf_data = resize_doc.tobytes()
        raw_pdf = io.BytesIO(pdf_data)
        raw_pdf_size = raw_pdf.getbuffer().nbytes
        minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                object_name = object_key['pdf-path'], 
                                data = raw_pdf, 
                                length= raw_pdf_size,
                                content_type = 'application/pdf')
        
        page_preprocess_response = requests.post(f"{APP_HOST}/api/preprocess/page", data={'pageId': page_id})
    except Exception as e:
        print('split book', e)
        return "error"