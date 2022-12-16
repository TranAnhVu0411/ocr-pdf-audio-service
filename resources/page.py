from flask import Response, request
from flask_restful import Resource
from database.models import Chapters, Pages
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
            body = request.get_json()
            Pages.objects.get(id=page_id).update(**body)
            return 'successful', 200
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError