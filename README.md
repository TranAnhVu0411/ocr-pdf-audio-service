# OCR PDF Audio Service
(Will dockerize this project later)

Book PDF and Audio Management Service for Audiobook Website

git clone this respitory

git clone https://github.com/TranAnhVu0411/audiobook-project and complete the setup

install mongodb

install minio in your computer
+ Window: https://min.io/docs/minio/windows/index.html
+ Mac: https://min.io/docs/minio/macos/index.html

install rabbitmq in your computer

Add .env file in code, specifically:
+ in main project, add file .env with content:
MONGODB_SETTINGS={
    'db':'audiobook_db',
    'host':'localhost',
    'port': 27017,
    'alias':'default'
}
+ in cloud folder, add file .env with content:
HOST= localhost:9000
ACCESS_KEY=********
SECRET_KEY=********
BASE_BUCKET=audiobook

In terminal:
+ go to project and run pip install -r requirements.txt

+ run minio: minio server start (This one is run in Mac, hasn't checked in Window yet) => open localhost:9000 and create bucket named "audiobook"

+ run rabbitMQ: brew services restart rabbitmq (This one is run in Mac, hasn't checked in Window yet)

+ run server: python -u "run.py"

+ run celery: celery -A app.celery_pdf_process worker --loglevel=INFO
