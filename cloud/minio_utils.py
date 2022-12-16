from datetime import *

from dotenv import dotenv_values
from minio import Minio
from minio.datatypes import PostPolicy

config = dotenv_values("cloud/.env.cloud")

print(config)

minio_client = Minio(
    endpoint=config["HOST"],
    access_key=config["ACCESS_KEY"],
    secret_key=config["SECRET_KEY"],
    secure=False
)

def create_if_not_found(bucket_name):
    try:
        if minio_client.bucket_exists(f"{config['BASE_BUCKET']}/{bucket_name}"):
            return True
        else:
            minio_client.make_bucket(f"{config['BASE_BUCKET']}/{bucket_name}")
            return True
    except Exception as e:
        return False

def get_presigned_url(object_key, expires_hours = 2 ):
    try:
        url = minio_client.get_presigned_url(
            "PUT",
            config['BASE_BUCKET'],
            object_key,
            expires=timedelta(hours=expires_hours),
            response_headers={"Content-Type": 'application/json'},
        )
        return url
    except Exception as e:
        print(e.message)
        return None

def get_image_get_presigned_url(object_key, expires_hours = 2 ):
    try:
        url = minio_client.get_presigned_url(
            "GET",
            config['BASE_BUCKET'],
            object_key,
            expires=timedelta(hours=expires_hours),
            response_headers={"response-content-type": "image/png"},
        )
        return url
    except Exception as e:
        print(e.message)
        return None

def get_pdf_get_presigned_url(object_key, expires_hours = 2 ):
    try:
        url = minio_client.get_presigned_url(
            "GET",
            config['BASE_BUCKET'],
            object_key,
            expires=timedelta(hours=expires_hours),
            response_headers={"response-content-type": "application/pdf"},
        )
        return url
    except Exception as e:
        print(e.message)
        return None