from celery import Celery
from os import environ
from neuroscout.app import app
celery_app = Celery('tasks', broker=environ.get('CELERY_BROKER_URL'),
             backend=environ.get('CELERY_RESULT_BACKEND'), include=['tasks'])

app.app_context().push()
