from flask import Response, request
from flask_restful import Resource
from database.models import Chapters, Books
import json

# post chapter và lấy thông tin của tất cả các chapter
class ChaptersApi(Resource):
    def post(self):
        body = request.form.to_dict(flat=False)
        upload_type = body.pop('uploadType')
        book_id = body.pop('bookId')
        book = Books.objects.get(id=book_id[0])
        # Trong trường hợp nếu upload PDF sách
        if upload_type[0]=='pdf':
            chapter_instances = []
            for chap in body['chapters']:
                temp = json.loads(chap)
                chapter_instances.append(Chapters(**{
                    "index": int(temp["chapterIndex"]),
                    "name": temp["chapterName"],
                    "fromPage": int(temp["chapterPageFrom"]),
                    "toPage": int(temp["chapterPageTo"]),
                    "status": "notready",
                    "uploadType": upload_type[0]
                }, book=book))    
            Chapters.objects.insert(chapter_instances, load_bulk=False)
            return 'success', 200
        # Trong trường hợp nếu upload ảnh của từng chương
        elif upload_type[0]=='image':
            params = json.loads(body['chapter'][0])
            chapter =Chapters(**{
                "index": int(params["chapterIndex"]),
                "name": params["chapterName"],
                "uploadType": upload_type[0]
            }, book=book)
            chapter.save()
            id = chapter.id
            return {'chapterId': str(id)}, 200
        else:
            return 'Something wrong happen in the body structure', 500