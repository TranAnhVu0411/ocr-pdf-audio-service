from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

def make_celery(app, host):
    celery = Celery('worker',
             broker=f'amqp://guest:guest@{host}:5672',
             backend=f'mongodb://{host}:27017/task_management',
             include=['tasks.ocr_tasks', 'tasks.pdf_tasks', 'tasks.audio_tasks', 'tasks.chapter_tasks'])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery