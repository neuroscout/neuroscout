from celery import Celery
from neuroscout.basic import create_app

celery_app = Celery('tasks')

# Push db context
flask_app, cache = create_app()
flask_app.app_context().push()
