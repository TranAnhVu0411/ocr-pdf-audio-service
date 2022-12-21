from flask import Response, request, make_response, jsonify
from flask_restful import Resource
from database.models import Chapters, Pages, Sentences
from cloud.minio_utils import *
from mongoengine.errors import (DoesNotExist, FieldDoesNotExist,
                                InvalidQueryError, NotUniqueError,
                                ValidationError)
from resources.errors.page_errors import (DeletingPageError, InternalServerError,
                                   PageAlreadyExistsError, PageNotExistsError,
                                   SchemaValidationError, UpdatingPageError)

# route api/pages
class PagesApi(Resource):
    def post(self):
        try:
            body = request.form.to_dict()
            chapter_id = body.pop('chapterId')
            chapter = Chapters.objects.get(id=chapter_id)
            page = Pages(**{
                "index": int(body["index"]),
            }, chapter=chapter)   
            page.save()
            id = page.id
            return {'pageId': str(id)}, 200
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise PageAlreadyExistsError
        except Exception as e:
            raise InternalServerError

# route api/pages/<page_id>
class PageApi(Resource):
    def put(self, page_id):
        try:
            body = request.form.to_dict()
            body = request.get_json()
            page = Pages.objects.get(id=page_id)
            # Thêm sentence vào list sentence
            if 'sentenceId' in body:
                sentence = Sentences.objects.get(id=body['sentenceId'])
                page.update(push__sentences = sentence)
                return 'add sentence successful', 200
            # Cập nhật các thông tin khác trong trang
            else:
                page.update(**body)
                return 'update successful', 200
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError
    def get(self, page_id):
        try:
            page = Pages.objects.get(id=page_id)
            sentences = Sentences.objects(page=page_id)
            return make_response(jsonify({'page': page, 'sentences': sentences}), 200)
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError