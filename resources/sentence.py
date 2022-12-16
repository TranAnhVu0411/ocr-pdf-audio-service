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
    def get(self, id):
        # id == page_id
        try:
            sentence_list = Sentences.objects.filter(page=id)
            return make_response(jsonify({'sentence_list': sentence_list}), 200)
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError
    def put(self, id):
        # id == sentence_id
        try:
            body = request.form.to_dict()
            sentence = Sentences.objects.get(id=id)
            sentence.update(**body)
            return 'successful', 200
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingPageError
        except Exception:
            raise InternalServerError