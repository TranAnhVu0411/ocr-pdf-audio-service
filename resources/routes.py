from .book import BooksApi
from .url import PresignedUrlApi, ObjectKeyApi
from .chapter import ChaptersApi, ChapterApi, ChapterGetAllApi
from .page import PagesApi, PageApi
from .sentence import SentencesApi, SentenceApi
from .tasks import PageImgProcessApi, BookPdfProcessApi, PageAudioProcessApi, ChapterProcessApi

# from .reset_password import ForgotPassword, ResetPassword


def initialize_routes(api):
    api.add_resource(BooksApi, '/api/books/<book_id>')

    api.add_resource(ChaptersApi, '/api/chapters')
    api.add_resource(ChapterApi, '/api/chapters/<chapter_id>')
    api.add_resource(ChapterGetAllApi, '/api/chapter_meta/<chapter_id>')

    api.add_resource(PagesApi, '/api/pages')
    api.add_resource(PageApi, '/api/pages/<page_id>')

    api.add_resource(SentencesApi, '/api/sentences')
    api.add_resource(SentenceApi, '/api/sentences/<sentence_id>')

    api.add_resource(PresignedUrlApi, '/api/urls')
    api.add_resource(ObjectKeyApi, '/api/object_keys')

    api.add_resource(PageImgProcessApi, '/api/preprocess/page')
    api.add_resource(BookPdfProcessApi, '/api/preprocess/book')
    api.add_resource(PageAudioProcessApi, '/api/preprocess/audio')
    api.add_resource(ChapterProcessApi, '/api/preprocess/chapter/<chapter_id>')