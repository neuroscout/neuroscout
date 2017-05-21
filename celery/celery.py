from celery import Celery
app = Celery('test_celery', broker='redis://redis:6379/0',
             backend='redis://redis:6379/0', include=['tasks'])
