from datetime import *

from dotenv import dotenv_values
from minio import Minio
from minio.datatypes import PostPolicy
from minio.error import S3Error

config = dotenv_values("cloud/.env")

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

def get_presigned_url(object_key, type, response_type, expires_hours = 24 ):
    try:
        url = minio_client.get_presigned_url(
            type,
            config['BASE_BUCKET'],
            object_key,
            expires=timedelta(hours=expires_hours),
            response_headers={"Content-Type": response_type},
        )
        return url
    except Exception as e:
        print(e.message)
        return None

def check_object_exist(object_key):
    try:
        minio_client.stat_object(config['BASE_BUCKET'], object_key)
        return True
    except Exception as e:
        print(e)
        return False