from celery import Celery
from os import environ
from neuroscout.basic import create_app

celery_app = Celery(
    'tasks', broker=environ.get('CELERY_BROKER_URL'),
    backend=environ.get('CELERY_RESULT_BACKEND'),
    include=['tasks', 'upload'])


# Push db context
flask_app, cache = create_app()
flask_app.app_context().push()
