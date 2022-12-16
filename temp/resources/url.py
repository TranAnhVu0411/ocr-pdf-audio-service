from flask import Response, request
from flask_restful import Resource
from database.models import Chapters, Pages
from cloud.minio_utils import *
import os

# Presigned Url API
class UrlApi(Resource):
    def post(self):
        pass