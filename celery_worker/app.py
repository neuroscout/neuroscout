from celery import Celery
from neuroscout.basic import create_app
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init("https://8d72e53e214c4ae1af7e34fa776659d8@sentry.io/1783101", integrations=[CeleryIntegration()])

celery_app = Celery('tasks')

# Push db context
flask_app, cache = create_app()
flask_app.app_context().push()
