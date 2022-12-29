# from pydub import AudioSegment
# from io import BytesIO
# from gtts import gTTS
# from app import celery_pdf_process
# from database.models import Sentences, Pages, Chapters
# from cloud.minio_utils import *
# import requests
# from database.models import *

# APP_HOST = 'http://localhost:3500'

# @celery_pdf_process.task()
# def create_chapters_pdf():
#     try:
#         status_response = requests.get(f"{APP_HOST}/api/chapters")
