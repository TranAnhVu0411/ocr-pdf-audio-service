from flask import Response, request, make_response, jsonify
from flask_restful import Resource
from database.models import Chapters, Books, Pages, Sentences, Status
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

# Hàm check status của chapters
def check_status(pages, attribute):
    if any(page[attribute] == Status.ERROR for page in pages):
        return "error"
    elif all(page[attribute] == Status.READY for page in pages):
        return "ready"
    elif any(page[attribute] == Status.PROCESSING for page in pages):
        return "processing"
    else:
        return "new"

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
    
    # Lấy thông tin chapter + pages + status (Phục vụ cho task)
    def get(self, chapter_id):
        mongo = get_connection()
        with mongo.start_session() as session:
            with session.start_transaction():
                try:
                    query = request.args.to_dict()
                    print(query)
                    chapter = Chapters.objects.get(id=chapter_id)
                    if ('state' in query):
                        if query['state'] =='previous':
                            previous_chapter = Chapters.objects.get(book=chapter.book, index=chapter.index-1)
                            pages = Pages.objects(chapter=previous_chapter.id).order_by('index')
                            pdf_status = check_status(pages, 'pdfStatus')
                            audio_status = check_status(pages, 'audioStatus')
                            return make_response(jsonify({'chapter': previous_chapter, 'pdfStatus': pdf_status, 'audioStatus': audio_status}), 200)
                        elif query['state'] =='next':
                            next_chapter = Chapters.objects.get(book=chapter.book, index=chapter.index+1)
                            pages = Pages.objects(chapter=next_chapter.id).order_by('index')
                            pdf_status = check_status(pages, 'pdfStatus')
                            audio_status = check_status(pages, 'audioStatus')
                            return make_response(jsonify({'chapter': next_chapter, 'pdfStatus': pdf_status, 'audioStatus': audio_status}), 200)
                    else:
                        pages = Pages.objects(chapter=chapter_id).order_by('index')
                        pdf_status = check_status(pages, 'pdfStatus')
                        audio_status = check_status(pages, 'audioStatus')
                        return make_response(jsonify({'chapter': chapter, 'pages': pages, 'pdfStatus': pdf_status, 'audioStatus': audio_status}), 200)
                except (FieldDoesNotExist, ValidationError):
                    session.abort_transaction()
                    raise SchemaValidationError
                except NotUniqueError:
                    session.abort_transaction()
                    raise ChapterAlreadyExistsError
                except Exception as e:
                    session.abort_transaction()
                    raise InternalServerError
                    
# route api/chapter_meta/<chapter_id>
class ChapterGetAllApi(Resource):
    # Lấy toàn bộ thông tin chapter (chapter, pages, sentences)
    # Cấu trúc 
    # Lưu ý: Trong bounding box, các thông số lấy theo % của page (hiện tại đang set mặc định A4: width=595, height=842)
    # {
    #     chapter: <chapter_info>,
    #     sentences: [
    #         {
    #             page_index: ,
    #             sentence_id: ,
    #             text: ,
    #             start_time: ,
    #             bounding_boxes: [
    #                 {
    #                     x: ,
    #                     y: ,
    #                     width: ,
    #                     height: ,
    #                     page_index: 
    #                 }
    #             ]
    #         }
    #     ]
    # }
    def get(self, chapter_id):
        mongo = get_connection()
        with mongo.start_session() as session:
            with session.start_transaction():
                try:
                    chapter = Chapters.objects.get(id=chapter_id)
                    num_chapter = len(Chapters.objects(book=chapter.book))
                    pages = Pages.objects(chapter=chapter_id).order_by('index')
                    sentence_list = []
                    time_between_sentence = 0.048 # Thời gian giữa 2 câu
                    total_time = 0
                    for i in pages:
                        sentences = Sentences.objects(page=i.id).order_by('index')
                        for j in sentences:
                            total_time += j['audioLength']
                            sentence_item = {}
                            sentence_item['pageIndex'] = i['index']-1
                            sentence_item['sentenceId'] = str(j['id'])
                            sentence_item['endTime'] = total_time
                            sentence_item['duration'] = j['audioLength']
                            total_time += time_between_sentence
                            bounding_box_list = []
                            for k in j['boundingBox']:
                                bounding_box_list.append({
                                    'pageIndex': i['index']-1,
                                    'left': (k['x']/595)*100,
                                    'top': (k['y']/842)*100,
                                    'width': (k['width']/595)*100,
                                    'height': (k['height']/842)*100
                                })
                            sentence_item['highlightAreas'] = bounding_box_list
                            sentence_list.append(sentence_item)
                    return make_response(jsonify({'chapter': chapter, 'numChapter': num_chapter,'sentences': sentence_list}), 200)
                except (FieldDoesNotExist, ValidationError):
                    session.abort_transaction()
                    raise SchemaValidationError
                except NotUniqueError:
                    session.abort_transaction()
                    raise ChapterAlreadyExistsError
                except Exception as e:
                    session.abort_transaction()
                    raise InternalServerError