from flask import Response, request
from flask_restful import Resource
from database.models import Chapters, Pages
from cloud.minio_utils import *
import os

# post page
class PagesApi(Resource):
    def post(self):
        body = request.form.to_dict()
        chapter_id = body.pop('chapterId')
        chapter = Chapters.objects.get(id=chapter_id)
        page_instances = []
        for index in range(int(body['numPages'])):
            page_instances.append(Pages(**{
                "index": index+1,
            }, chapter=chapter))    
        pages = Pages.objects.insert(page_instances, load_bulk=False)
        chapter_path = chapter.get_chapter_folder_path()
        url_list = []
        for i in pages:
            id = str(i)
            path = os.path.join(chapter_path, f"page_{id}/page_{id}.png")
            url = post_presigned_url(path, 'image/png')
            url_list.append(url)
        return {'urls': url_list}, 200