from pydub import AudioSegment
from io import BytesIO
from gtts import gTTS
import fitz
from app import celery_pdf_process
from database.models import Sentences, Pages, Chapters
from cloud.minio_utils import *
import requests
from database.models import *
from .utils.audio_utils import *
import json

APP_HOST = 'http://localhost:3500'

# Kiểm tra trạng thái của chapters
# Nếu toàn bộ các page trong chapters đều sẵn sàng => tạo pdf/audio cho chapter
# Nếu không => chưa tạo
@celery_pdf_process.task()
def get_pdf_audio_obj_key(chapter_id):
    try:
        get_response = requests.get(f"{APP_HOST}/api/chapters/{chapter_id}")
        state = get_response.json()

        if (state['pdfStatus']=='ready' and state['audioStatus']=='ready'):
            chapter_key_res = requests.post(f"{APP_HOST}/api/object_keys", data={'type': 'chapter', 'id': chapter_id})
            page_key_list = []
            for page in state['pages']:
                page_key_res = requests.post(f"{APP_HOST}/api/object_keys", data={'type': 'page', 'id': page['_id']['$oid']})
                page_key_list.append(page_key_res.json())
            return json.dumps({
                'chapter_obj_keys': chapter_key_res.json(),
                'page_key_list': page_key_list
            })
        else:
            return 'incomplete'
    except Exception as e:
        print('get obj key task', e)

@celery_pdf_process.task()
def concat_audio(object_key_metadata):
    if object_key_metadata!= 'incomplete':
        try:
            object_key = json.loads(object_key_metadata)
            chapter_audio_object_key = object_key['chapter_obj_keys']['audio-path']
            page_audio_object_key_list = [keys['audio-path'] for keys in object_key['page_key_list']]

            audio_segment_list = []
            for object_key in page_audio_object_key_list:
                response = minio_client.get_object(config["BASE_BUCKET"], object_key)
                audio_segment_list.append(AudioSegment.from_file(BytesIO(response.data), format="mp3"))
            audio = merge_audio_segments(audio_segment_list)
            raw_audio = BytesIO()
            audio.export(raw_audio, format="mp3")
            raw_audio_size = raw_audio.getbuffer().nbytes
            minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                    object_name = chapter_audio_object_key, 
                                    data = raw_audio, 
                                    length= raw_audio_size,
                                    content_type = 'audio/mpeg')
            return "success"
        except Exception as e:
            print('chapter audio task', e)
    else: 
        return 'incomplete'

@celery_pdf_process.task()
def concat_pdf(object_key_metadata):
    if object_key_metadata!= 'incomplete':
        try:
            object_key = json.loads(object_key_metadata)
            chapter_pdf_object_key = object_key['chapter_obj_keys']['pdf-path']
            page_pdf_object_key_list = [keys['pdf-path'] for keys in object_key['page_key_list']]

            chapter_doc = fitz.open()
            for object_key in page_pdf_object_key_list:
                response = minio_client.get_object(config["BASE_BUCKET"], object_key)
                doc = fitz.open("pdf", response.data)
                chapter_doc.insert_pdf(doc)
            pdf_data = chapter_doc.tobytes()
            raw_pdf = BytesIO(pdf_data)
            raw_pdf_size = raw_pdf.getbuffer().nbytes
            minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                    object_name = chapter_pdf_object_key, 
                                    data = raw_pdf, 
                                    length= raw_pdf_size,
                                    content_type = 'application/pdf')
            return "success"
        except Exception as e:
            print('chapter pdf task', e)
    else: 
        return 'incomplete'
