import pytesseract
from PIL import Image
import io
from cloud.minio_utils import *
from app import celery_pdf_process
import requests
from database.models import *

APP_HOST = 'http://localhost:3500'


# If you don't have tesseract executable in your PATH, include the following:
# MacOS
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/Cellar/tesseract/5.2.0/bin/tesseract'

@celery_pdf_process.task()
def create_ocr_page(page_id, ocr_status, page_img_object_key, page_pdf_object_key):
    if ocr_status == Status.NEW:
        try:
            response = minio_client.get_object(config["BASE_BUCKET"], page_img_object_key)
            img = Image.open(response)
            pdf = pytesseract.image_to_pdf_or_hocr(img, extension='pdf',lang="vie")
            raw_pdf = io.BytesIO(pdf)
            raw_pdf_size = raw_pdf.getbuffer().nbytes
            minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                    object_name = page_pdf_object_key, 
                                    data = raw_pdf, 
                                    length= raw_pdf_size,
                                    content_type = 'application/pdf')
            
            update_response = requests.put(
                f"{APP_HOST}/api/pages/{page_id}", 
                json = {
                    "ocrStatus": Status.READY, 
                    "pdfStatus": Status.PROCESSING, 
                    "imageStatus": Status.PROCESSING
                })
            return update_response.status_code
        except Exception as e:
            requests.put(f"{APP_HOST}/api/pages/{page_id}", json = {"ocrStatus": Status.ERROR})
    elif ocr_status == Status.READY:
        return 'ocr is already completed'
    



