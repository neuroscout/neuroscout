# from test_celery.celery import app
import time

from celery import Celery
app = Celery('tasks', broker='redis://redis:6379/0',
             backend='redis://redis:6379/0')


@app.task(name='mytasks.add')
def add(x, y):
    time.sleep(5) # lets sleep for a while before doing the gigantic addition task!
    return x + y
