from flask import Response, request
from flask_restful import Resource
from database.models import Chapters, Pages, Books
from celery import group, chain
from tasks.ocr_tasks import *
from tasks.pdf_tasks import *
from tasks.audio_tasks import *
from database.models import *

# Xử lý OCR, Audio cho Page Image
class PageImgProcessApi(Resource):
    def post(self):
        body = request.form.to_dict()
        page_id = body.pop('pageId')
        page = Pages.objects.get(id=page_id)
        ocr_status = page['ocrStatus']
        image_status = page['imageStatus']

        work_flow = chain(
            create_ocr_page.si(
                page_id = page_id,
                ocr_status = ocr_status, 
                page_img_object_key = page.get_page_image_path(), 
                page_pdf_object_key = page.get_page_pdf_path(),
            ), 
            get_pdf.si(pdf_object_key = page.get_page_pdf_path()), 
            group([
                bounding_box_preprocess.s(page_id=page_id), 
                convert_pdf_to_image.s(
                    page_id = page_id, 
                    image_status = image_status,
                    page_img_object_key = page.get_page_image_path(), 
                )
            ]), 
            text_to_speech.si(
                page_id = page_id, 
                page_audio_object_key = page.get_page_audio_path()
            )
        ).apply_async()
        return {'work_flow_id': work_flow.id}, 200

# Xử lý Split trang cho sách
class BookPdfProcessApi(Resource):
    def post(self):
        body = request.form.to_dict()
        book = Books.objects.get(id=body['bookId'])
        chapter_list = json.loads(body['chapterList'])
        print(chapter_list)

        work_flow = chain(
            get_pdf.si(pdf_object_key = book.get_book_pdf_path()),
            group(
                split_book_page.s(
                    from_page = int(chapter['from']), 
                    to_page = int(chapter['to']),
                    chapter_id = chapter['chapterId']
                ) for chapter in chapter_list)
        ).apply_async()

        return {'work_flow_id': work_flow.id}, 200