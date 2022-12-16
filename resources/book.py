from flask import Response, request, jsonify, make_response
from flask_restful import Resource
from database.models import Books
from database.models import Chapters
from cloud.minio_utils import *

# Upload pdf sách và thay đổi trạng thái của sách từ available sang waiting
class BooksApi(Resource):
    def get(self, book_id):
        chapters = Chapters.objects(book=book_id).order_by('index')
        
        return make_response(jsonify(chapters), 200)

class PresignedURLApi(Resource):
    def get(self, book_id):
        book = Books.objects.get(id=book_id)
        path = book.get_book_pdf_path()
        url = post_presigned_url(path, 'application/json')
        return make_response({'url': url}, 200)
        
        
        
    