from .book import BooksApi, PresignedURLApi
from .chapter import ChaptersApi
from .page import PagesApi

# from .reset_password import ForgotPassword, ResetPassword


def initialize_routes(api):
    api.add_resource(BooksApi, '/api/books/<book_id>')
    api.add_resource(PresignedURLApi, '/api/books/pdf/<book_id>')
    api.add_resource(ChaptersApi, '/api/chapters')
    api.add_resource(PagesApi, '/api/pages')