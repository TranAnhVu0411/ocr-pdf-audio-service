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
    return (round(x0), round(y0)), (round(x1), round(y1))

# Lấy các câu
def get_text(wordList):
    text = ""
    for (idx, word) in enumerate(wordList):
        text+=word[4]+" "
        if idx == len(wordList)-1:
            text+=word[4]
    return text

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

# Đọc PDF
@celery_pdf_process.task()
def get_pdf(pdf_object_key): # id: mã sách/trang , type: book/page
    response = minio_client.get_object(config["BASE_BUCKET"], pdf_object_key)
    doc = fitz.open("pdf", response.data)
    doc_bytes = doc.tobytes()
    base64_doc_bytes = base64.b64encode(doc_bytes)
    return base64_doc_bytes.decode('ascii')

@celery_pdf_process.task()
def bounding_box_preprocess(doc_message, page_id):
    try:
        base64_doc_bytes = doc_message.encode('ascii')
        doc_bytes = base64.b64decode(base64_doc_bytes)
        doc = fitz.open(stream=doc_bytes, filetype="pdf")
        
        page = doc[0]
        sentences = read_page(page)
        page = Pages.objects.get(id=page_id)
        for (sentenceIdx, wordList) in enumerate(sentences):
            # Tạo sentence object và lưu vào csdl
            text = get_text(wordList)
            boundingBoxList = []
            startPoints, endPoints = merge_bounding_box(wordList)        
            for (startPoint, endPoint) in zip(startPoints, endPoints):
                boundingBoxList.append(convert_bb_type(startPoint, endPoint))
            create_response = requests.post(f"{APP_HOST}/api/sentences", data={"index": sentenceIdx, "text": text, "boundingBox": json.dumps(boundingBoxList), "pageId": page_id})
            sentence_id = create_response.json()
            update_list_response = requests.put(f"{APP_HOST}/api/pages/{page_id}", json=sentence_id)

        # Update trạng thái trang
        update_status_response = requests.put(f"{APP_HOST}/api/pages/{page_id}", json = {"pdfStatus": Status.READY, "audioStatus": Status.PROCESSING})
        return update_status_response.status_code
    except Exception as e:
        requests.put(f"{APP_HOST}/api/pages/{page_id}", json = {"pdfStatus": Status.ERROR})

@celery_pdf_process.task()
def convert_pdf_to_image(doc_message, page_id, page_img_object_key):
    try:
        base64_doc_bytes = doc_message.encode('ascii')
        doc_bytes = base64.b64decode(base64_doc_bytes)
        doc = fitz.open(stream=doc_bytes, filetype="pdf")

        pix = doc[0].get_pixmap()
        data = pix.pil_tobytes(format="png", optimize=True)
        raw_img = io.BytesIO(data)
        raw_img_size = raw_img.getbuffer().nbytes
        minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                object_name = page_img_object_key, 
                                data = raw_img, 
                                length= raw_img_size,
                                content_type = 'image/png')
        update_response = requests.put(f"{APP_HOST}/api/pages/{page_id}", json = {"imageStatus": Status.READY})
        return update_response.status_code
    except Exception as e:
        requests.put(f"{APP_HOST}/api/pages/{page_id}", json = {"imageStatus": Status.ERROR})

@celery_pdf_process.task()
def split_book_page(doc_message, from_page, to_page, chapter_id):
    base64_doc_bytes = doc_message.encode('ascii')
    doc_bytes = base64.b64decode(base64_doc_bytes)
    doc = fitz.open(stream=doc_bytes, filetype="pdf")

    chapter = Chapters.objects.get(id=chapter_id)
    chapter_path = chapter.get_chapter_folder_path()
    for (idx, i) in enumerate(range(from_page-1, to_page)):
        # Tạo Page và lưu vào db
        page = Pages(**{
            "index": idx+1,
            "status": 'processing_highlight'
        }, chapter=chapter)   
        page.save()
        # Upload ảnh lên Cloud
        pix = doc[i].get_pixmap()
        img_data = pix.pil_tobytes(format="png", optimize=True)
        raw_img = io.BytesIO(img_data)
        raw_img_size = raw_img.getbuffer().nbytes
        minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                object_name = page.get_page_image_path(chapter_path), 
                                data = raw_img, 
                                length= raw_img_size,
                                content_type = 'image/png')
        # Upload PDF lên Cloud
        pdf_data = doc[i].tobytes()
        raw_pdf = io.BytesIO(pdf_data)
        raw_pdf_size = raw_pdf.getbuffer().nbytes
        minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                object_name = page.get_page_pdf_path(chapter_path), 
                                data = raw_pdf, 
                                length= raw_pdf_size,
                                content_type = 'application/pdf')