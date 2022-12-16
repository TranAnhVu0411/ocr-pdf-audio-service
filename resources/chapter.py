from flask import Response, request
from flask_restful import Resource
from database.models import Chapters, Books, Pages
import json
from mongoengine.errors import (DoesNotExist, FieldDoesNotExist,
                                InvalidQueryError, NotUniqueError,
                                ValidationError)
from resources.errors.chapter_errors import (ChapterAlreadyExistsError,
                                             ChapterNotExistsError,
                                             DeletingChapterError,
                                             InternalServerError,
                                             SchemaValidationError,
                                             UpdatingChapterError)
from mongoengine.connection import get_connection

# route api/chapters
class ChaptersApi(Resource):
    def post(self):
        mongo = get_connection()
        with mongo.start_session() as session:
            with session.start_transaction():
                try:
                    body = request.form.to_dict()
                    book_id = body.pop('bookId')
                    book = Books.objects.get(id=book_id)
                    chapter = Chapters(**{
                        "index": int(body["index"]),
                        "name": body["name"],
                    }, book=book)
                    chapter.save(session=session)
                    id = chapter.id
                    return {'chapterId': str(id)}, 200
                except (FieldDoesNotExist, ValidationError):
                    session.abort_transaction()
                    raise SchemaValidationError
                except NotUniqueError:
                    session.abort_transaction()
                    raise ChapterAlreadyExistsError
                except Exception as e:
                    session.abort_transaction()
                    raise InternalServerError

# route api/chapters/<chapter_id>
class ChapterApi(Resource):
    def put(self, chapter_id):
        mongo = get_connection()
        with mongo.start_session() as session:
            with session.start_transaction():
                try:
                    body = request.form.to_dict()
                    chapter = Chapters.objects.get(id=chapter_id)
                    if 'pageId' in body:
                        page = Pages.objects.get(id=body['pageId'])
                        chapter.update(push__pages = page)
                        return 'add page successful', 200
                    else:
                        chapter.update(**body)
                        return 'update successful', 200
                except (FieldDoesNotExist, ValidationError):
                    session.abort_transaction()
                    raise SchemaValidationError
                except NotUniqueError:
                    session.abort_transaction()
                    raise ChapterAlreadyExistsError
                except Exception as e:
                    session.abort_transaction()
                    raise InternalServerError
                    