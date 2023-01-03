from io import BytesIO
from app import celery_pdf_process
from cloud.minio_utils import *
import requests
from database.models import *
from .utils.audio_utils import *

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

APP_HOST = 'http://localhost:3500'

@celery_pdf_process.task()
def text_to_speech(page_id, page_audio_object_key):
    try:
        get_response = requests.get(f"{APP_HOST}/api/pages/{page_id}")
        sentence_list = get_response.json()['sentences']
        audio_segment_list = []
        for sentence in sentence_list:
            text = sentence['text']
            id = sentence['_id']['$oid']
            audio_segment = convert_text_to_pydub_audio_segment(text)
            audio_segment_list.append(audio_segment)
            audio_length = audio_segment.duration_seconds
            get_response = requests.put(f"{APP_HOST}/api/sentences/{id}", data = {"audioLength": audio_length})

        main_audio = merge_audio_segments(audio_segment_list)
        raw_audio = BytesIO()
        main_audio.export(raw_audio, format="mp3")
        raw_audio_size = raw_audio.getbuffer().nbytes
        minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                                object_name = page_audio_object_key, 
                                data = raw_audio, 
                                length= raw_audio_size,
                                content_type = 'audio/mpeg')
        update_response = requests.put(f"{APP_HOST}/api/pages/{page_id}", data = {"audioStatus": Status.READY})
        return update_response.status_code
    except Exception as e:
        print('audio task', e)
        requests.put(f"{APP_HOST}/api/pages/{page_id}", data = {"audioStatus": Status.ERROR})