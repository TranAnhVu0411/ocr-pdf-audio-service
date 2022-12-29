from flask import Response, request, make_response, jsonify
from flask_restful import Resource
from database.models import Chapters, Books, Pages, Sentences
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
    # Tạo chapter mới
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
                    # Nếu trong request có from, to là trang bắt đầu và trang kết thúc trong pdf
                    if 'from' in body:
                        return {'chapterId': str(id), 'from': body['from'], 'to': body['to']}, 200
                    # Nếu không có, chỉ truyền chapterId
                    else:
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
    # Lấy trạng thái của tất cả các chapters
    # def get(self):
    #     try:
    #         chapters = Chapters.objects()
            
    #         return {'chapterId': str(id)}, 200
    #     except (FieldDoesNotExist, ValidationError):
    #         raise SchemaValidationError
    #     except NotUniqueError:
    #         raise ChapterAlreadyExistsError
    #     except Exception as e:
    #         raise InternalServerError


# route api/chapters/<chapter_id>
class ChapterApi(Resource):
    # Cập nhật thông tin chapters
    def put(self, chapter_id):
        mongo = get_connection()
        with mongo.start_session() as session:
            with session.start_transaction():
                try:
                    body = request.form.to_dict()
                    chapter = Chapters.objects.get(id=chapter_id)
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
    
    # Lấy thông tin chapter + pages
    def get(self, chapter_id):
        mongo = get_connection()
        with mongo.start_session() as session:
            with session.start_transaction():
                try:
                    chapter = Chapters.objects.get(id=chapter_id)
                    pages = Pages.objects(chapter=chapter_id).order_by('index')
                    return make_response(jsonify({'chapter': chapter, 'pages': pages}), 200)
                except (FieldDoesNotExist, ValidationError):
                    session.abort_transaction()
                    raise SchemaValidationError
                except NotUniqueError:
                    session.abort_transaction()
                    raise ChapterAlreadyExistsError
                except Exception as e:
                    session.abort_transaction()
                    raise InternalServerError
                    
# route api/chapter/<chapter_id>
class ChapterGetAllApi(Resource):
    # Lấy toàn bộ thông tin chapter (chapter, pages, sentences)
    def get(self, chapter_id):
        mongo = get_connection()
        with mongo.start_session() as session:
            with session.start_transaction():
                try:
                    chapter = Chapters.objects.get(id=chapter_id)
                    pages = Pages.objects(chapter=chapter_id).order_by('index')
                    page_list = []
                    for i in pages:
                        sentences = Sentences.objects(page=i.id).order_by('index')
                        page_list.append({
                            'page': i, 'sentences': sentences})
                    return make_response(jsonify({'chapter': chapter, 'pages': page_list}), 200)
                except (FieldDoesNotExist, ValidationError):
                    session.abort_transaction()
                    raise SchemaValidationError
                except NotUniqueError:
                    session.abort_transaction()
                    raise ChapterAlreadyExistsError
                except Exception as e:
                    session.abort_transaction()
                    raise InternalServerError