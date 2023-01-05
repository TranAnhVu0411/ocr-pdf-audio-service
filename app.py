import os
os.environ['ENV_FILE_LOCATION'] = ".env"

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_cors import CORS
from tasks.worker import make_celery

from dotenv import dotenv_values

config = dotenv_values(".env")

app = Flask(__name__)
app.config.from_envvar('ENV_FILE_LOCATION')
CORS(app)

from database.db import initialize_db
initialize_db(app)

# celery_pdf_process = make_celery(app, config['BROKER_HOST'])
celery_pdf_process = make_celery(app, "localhost")

from resources.routes import initialize_routes
api = Api(app)
initialize_routes(api)
