from flask import Response, request, jsonify, make_response
from flask_restful import Resource
from database.models import *
from cloud.minio_utils import *
from mongoengine.errors import (DoesNotExist, FieldDoesNotExist,
                                InvalidQueryError, NotUniqueError,
                                ValidationError)
from resources.errors.page_errors import (DeletingPageError, InternalServerError,
                                   PageAlreadyExistsError, PageNotExistsError,
                                   SchemaValidationError, UpdatingPageError)
import json

# route api/sentences
class SentencesApi(Resource):
    # Tạo sentence mới
    def post(self):
        try:
            body = request.form.to_dict()
            # print(body)
            page_id = body.pop('pageId')
            page = Pages.objects.get(id=page_id)
            sentence = Sentences()
            sentence.page = page
            sentence.index = int(body['index']) 
            sentence.text = body['text']
            sentence.boundingBox = []
            for bb in json.loads(body['boundingBox']):
                bb_instance = BoundingBoxes(**bb)
                sentence.boundingBox.append(bb_instance)
            sentence.save()
            id = sentence.id
            return {'sentenceId': str(id)}, 200
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise PageAlreadyExistsError
        except Exception as e:
            raise InternalServerError

# route api/sentences/<page_id/sentence_id>
class SentenceApi(Resource):
    # Lấy thông tin sentences trong pages
    def get(self, id):
        # id == page_id
        try:
            sentence_list = Sentences.objects.filter(page=id).order_by('index')
            return make_response(jsonify({'sentence_list': sentence_list}), 200)
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError
    # Cập nhật thông tin sentence
    def put(self, id):
        # id == sentence_id
        try:
            body = request.form.to_dict()
            sentence = Sentences.objects.get(id=id)
            if 'boundingBox' in body:
                bodyBB = json.loads(body.pop('boundingBox'))
                print(type(bodyBB))
                boundingBox = []
                for bb in bodyBB:
                    bb_instance = BoundingBoxes(
                        x=bb['x'],
                        y=bb['y'],
                        width=bb['width'],
                        height=bb['height']
                    )
                    boundingBox.append(bb_instance)
                sentence.update(**body, boundingBox=boundingBox)
            else:
                sentence.update(**body)
                return 'successful', 200
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError
    # Xoá sentence
    def delete(self, id):
        # id == sentence_id
        try:
            sentence = Sentences.objects.get(id=id)
            sentence.delete()
            return 'delete successful', 200
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError