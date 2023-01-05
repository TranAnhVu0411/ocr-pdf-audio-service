from flask import Response, request, jsonify, make_response
from flask_restful import Resource
from database.models import Books, Chapters
from cloud.minio_utils import *

# routes api/books/<book_id>
# Lấy thông tin danh sách chương sách
class BooksApi(Resource):
    def get(self, book_id):
        book = Books.objects.get(id=book_id)
        chapters = Chapters.objects(book=book_id).order_by('index')
        return make_response(jsonify({"bookPdfStatus":check_object_exist(book.get_book_pdf_path()), "chapters": chapters}), 200)
        
        
    