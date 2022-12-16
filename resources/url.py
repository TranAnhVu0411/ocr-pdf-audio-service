from flask import Response, request
from flask_restful import Resource
from cloud.minio_utils import *
from database.models import Pages, Books

# Presigned Url API
# Request = {
#     type: book/page,
#     id: ...,
#     data-type: mp3, pdf, image
# }
class PresignedUrlApi(Resource):
    def post(self):
        body = request.form.to_dict()
        if body['type']=='page':
            page = Pages.objects.get(id=body['id'])
            chapter = page.chapter
            if body['data-type']=='image':
                path = page.get_page_image_path()
                url = get_presigned_url(path)
                return {'url': url}, 200
        elif body['type']=='book':
            book = Books.objects.get(id=body['id'])
            path = book.get_book_pdf_path()
            url = get_presigned_url(path)
            return {'url': url}, 200
