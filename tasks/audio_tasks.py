from pydub import AudioSegment
from io import BytesIO
from gtts import gTTS
from app import celery_pdf_process
from database.models import Sentences, Pages, Chapters
from cloud.minio_utils import *
import requests
import json

import sys
sys.path.append('/opt/homebrew/opt/ffmpeg')

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

APP_HOST = 'http://localhost:3500'

def convert_text_to_pydub_audio_segment(text, language="vi"):
    gtts_object = gTTS(text = text, 
                       lang = language,
                       slow = False)
    audio_bytes = BytesIO()
    gtts_object.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return AudioSegment.from_file(audio_bytes, format="mp3")

def merge_audio_segments(audio_segment_list):
    main_audio = audio_segment_list[0]
    for segment in audio_segment_list[1:]:
        main_audio += segment
    return main_audio

@celery_pdf_process.task()
def text_to_speech(page_id, page_audio_object_key):
    get_response = requests.get(f"{APP_HOST}/api/sentences/{page_id}")
    sentence_list = get_response.json()['sentence_list']
    audio_segment_list = []
    for sentence in sentence_list:
        text = sentence['text']
        id = sentence['_id']
        audio_segment = convert_text_to_pydub_audio_segment(text)
        audio_segment_list.append(audio_segment)
        audio_length = audio_segment.duration_seconds
        get_response = requests.put(f"{APP_HOST}/api/sentences/{id}", json={"audioLength": audio_length})

    main_audio = merge_audio_segments(audio_segment_list)
    raw_audio = BytesIO()
    main_audio.export(raw_audio, format="mp3")
    raw_audio_size = raw_audio.getbuffer().nbytes
    minio_client.put_object(bucket_name = config['BASE_BUCKET'], 
                            object_name = page_audio_object_key, 
                            data = raw_audio, 
                            length= raw_audio_size,
                            content_type = 'audio/mpeg')

