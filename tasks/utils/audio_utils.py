from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO

import sys
sys.path.append('/opt/homebrew/opt/ffmpeg')

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
