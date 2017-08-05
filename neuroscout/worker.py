from celery import Celery
from os import environ

celery_app = Celery('tasks', broker=environ.get('CELERY_BROKER_URL'),
             backend=environ.get('CELERY_RESULT_BACKEND'))
