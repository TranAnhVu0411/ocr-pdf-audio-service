from flask import Response, request
from flask_restful import Resource
from cloud.minio_utils import *
from database.models import Pages, Books, Chapters

# Presigned Url API
# Request = {
#     upload-type: PUT/GET/DELETE
#     type: book/page/chapter,
#     id: ...,
#     data-type: audio, pdf, image
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
                    path = page.get_page_audio_path()
                    url = get_presigned_url(path, type='GET', response_type='audio/mpeg')
                    return {'url': url}, 200
            elif body['type']=='chapter':
                chapter = Chapters.objects.get(id=body['id'])
                if body['data-type']=='pdf':
                    path = chapter.get_chapter_pdf_path()
                    url = get_presigned_url(path, type='GET', response_type='application/pdf')
                    return {'url': url}, 200
                if body['data-type']=='audio':
                    path = chapter.get_chapter_audio_path()
                    url = get_presigned_url(path, type='GET', response_type='audio/mpeg')
                    return {'url': url}, 200
            elif body['type']=='book':
                book = Books.objects.get(id=body['id'])
                path = book.get_book_pdf_path()
                url = get_presigned_url(path, type='GET', response_type='application/pdf')
                return {'url': url}, 200
        # get DELETE presigned url
        elif body['upload-type'] == 'DELETE':
            if body['type']=='page':
                page = Pages.objects.get(id=body['id'])
                response = {}
                image_path = page.get_page_image_path()
                # if object key not exist, next, else, get presiged url
                if check_object_exist(image_path):
                    response["image_url"] = get_presigned_url(image_path, type='DELETE', response_type='application/json')
                else:
                    response["image_url"] = "not exist"

                pdf_path = page.get_page_pdf_path()
                if check_object_exist(pdf_path):
                    response['pdf_url'] = get_presigned_url(pdf_path, type='DELETE', response_type='application/json')
                else:
                    response["pdf_url"] = "not exist"

                mp3_path = page.get_page_audio_path()
                if check_object_exist(mp3_path):
                    response['audio_url'] = get_presigned_url(mp3_path, type='DELETE', response_type='application/json')
                else:
                    response["audio_url"] = "not exist"
                folder_path = page.get_page_folder_path()
                response["folder_url"] = get_presigned_url(folder_path, type='DELETE', response_type='application/json')
                return response, 200

# Get Object Key API
# Request = {
#     type: book/chapter/page,
#     id: ...,
# }
class ObjectKeyApi(Resource):
    def post(self):
        body = request.form.to_dict()
        if body['type']=='book':
            book = Books.objects.get(id=body['id'])
            path = book.get_book_pdf_path()
            return {'path': path}, 200
        if body['type']=='chapter':
            chapter = Chapters.objects.get(id=body['id'])
            return {
                'pdf-path': chapter.get_chapter_pdf_path(),
                'audio-path': chapter.get_chapter_audio_path(),
            }
        elif body['type']=='page':
            page = Pages.objects.get(id=body['id'])
            return {
                'image-path': page.get_page_image_path(), 
                'pdf-path': page.get_page_pdf_path(),
                'audio-path': page.get_page_audio_path()
            }, 200
