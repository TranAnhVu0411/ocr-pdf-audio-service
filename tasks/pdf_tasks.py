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

APP_HOST = 'http://localhost:3500'

# Đọc 1 trang
def read_page(page):
    # Trích rút các câu
    sentences = []
    temp = []
    words = page.get_text("words", sort=False)
    for (idx, word) in enumerate(words):
        temp.append(word)
        if word[4][-1] in ['.', '!', '?']:
            sentences.append(temp)
            temp=[]
        if idx == len(words)-1:
            sentences.append(temp)
    return sentences

# Hàm tìm bounding box bao list các bounding box
def find_bounding_box(listStartPoints, listEndPoints):
    x0 = listStartPoints[0][0]
    y0 = min([i[1] for i in listStartPoints])
    x1 = listEndPoints[-1][0]
    y1 = max([i[1] for i in listEndPoints])
    return (x0, y0), (x1, y1)

# Hợp nhất bounding box của các từ trong câu thành các bounding box của các dòng
def merge_bounding_box(wordList):
    startPoints = [(word[0], word[1]) for word in wordList]
    endPoints = [(word[2], word[3]) for word in wordList]

    # Lưu nhóm các bounding box nằm trên cùng 1 dòng
    lineGroupStartPoints=[]
    lineGroupEndPoints=[]

    tempStartPoints=[startPoints[0]]
    tempEndPoints=[endPoints[0]]
    for i in range((len(startPoints)-1)):
        if startPoints[i+1][0]>startPoints[i][0]:
            tempStartPoints.append(startPoints[i+1])
            tempEndPoints.append(endPoints[i+1])
        else:
            lineGroupStartPoints.append(tempStartPoints)
            lineGroupEndPoints.append(tempEndPoints)
            tempStartPoints=[startPoints[i+1]]
            tempEndPoints=[endPoints[i+1]]
        if i == len(startPoints)-2:
            lineGroupStartPoints.append(tempStartPoints)
            lineGroupEndPoints.append(tempEndPoints)
    
    # Lưu bounding box sau khi đã được merge
    lineStartPoints=[]
    lineEndPoints=[]
    for (listStartPoints, listEndPoints) in zip(lineGroupStartPoints, lineGroupEndPoints):
        startPoint, endPoint = find_bounding_box(listStartPoints, listEndPoints)
        lineStartPoints.append(startPoint)
        lineEndPoints.append(endPoint)
    
    return lineStartPoints, lineEndPoints

# Chuyển thông tin bounding box từ top left/bottom right
# sang x_top_left/y_top_left/width/height
def convert_bb_type(startPoint, endPoint):
    return {'x': startPoint[0], 'y': startPoint[1], 'width': endPoint[0]-startPoint[0], 'height': endPoint[1]-startPoint[1]}

# Lấy các câu
def get_text(wordList):
    text = ""
    for (idx, word) in enumerate(wordList):
        if idx == len(wordList)-1:
            text+=word[4]
        else:
            text+=word[4]+" "
    return text

# Từ base64 chuyển thành file pdf
def convert_base64_to_pdf(doc_message):
    base64_doc_bytes = doc_message.encode('ascii')
    doc_bytes = base64.b64decode(base64_doc_bytes)
    doc = fitz.open(stream=doc_bytes, filetype="pdf")
    return doc


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

# Chia sách ra thành các trang
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

            # Upload ảnh lên Cloud
            pix = doc[i].get_pixmap()
            img_data = pix.pil_tobytes(format="png", optimize=True)
            raw_img = io.BytesIO(img_data)
            raw_img_size = raw_img.getbuffer().nbytes
            minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                    object_name = object_key['image-path'], 
                                    data = raw_img, 
                                    length= raw_img_size,
                                    content_type = 'image/png')

            # Upload PDF lên Cloud
            page_doc = fitz.open() # an empty pdf file is opened
            page_doc.insert_pdf(doc, from_page=i, to_page=i)
            pdf_data = page_doc.tobytes()
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