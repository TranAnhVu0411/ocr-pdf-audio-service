from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def make_celery(app):
    celery = Celery('worker',
             broker='amqp://guest:guest@localhost:5672',
             backend='mongodb://localhost:27017/task_management',
             include=['tasks.ocr_tasks', 'tasks.pdf_tasks', 'tasks.audio_tasks'])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery