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
        print(body)
        # get PUT presigned url
        if body['upload-type'] == 'PUT':
            if body['type']=='page':
                page = Pages.objects.get(id=body['id'])
                if body['data-type']=='image':
                    path = page.get_page_image_path()
                    url = get_presigned_url(path, type='PUT', response_type='application/json')
                    return {'url': url}, 200
            elif body['type']=='book':
                book = Books.objects.get(id=body['id'])
                path = book.get_book_pdf_path()
                url = get_presigned_url(path, type='PUT', response_type='application/json')
                return {'url': url}, 200
        # get GET presigned url
        elif body['upload-type'] == 'GET':
            if body['type']=='page':
                page = Pages.objects.get(id=body['id'])
                if body['data-type']=='image':
                    path = page.get_page_image_path()
                    url = get_presigned_url(path, type='GET', response_type='image/png')
                    return {'url': url}, 200
                if body['data-type']=='pdf':
                    path = page.get_page_pdf_path()
                    url = get_presigned_url(path, type='GET', response_type='application/pdf')
                    return {'url': url}, 200
                if body['data-type']=='audio':
                    path = page.get_page_mp3_path()
                    url = get_presigned_url(path, type='GET', response_type='audio/mpeg')
                    return {'url': url}, 200
            elif body['type']=='book':
                book = Books.objects.get(id=body['id'])
                path = book.get_book_pdf_path()
                url = get_presigned_url(path, type='GET', response_type='application/pdf')
                return {'url': url}, 200


