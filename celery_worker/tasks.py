import time
from app import celery_app
import os

@celery_app.task(name='workflow.create')
def add(x, y):
    time.sleep(5) # lets sleep for a while before doing the gigantic addition task!
    filename = "workflow_{}_{}.py".format(x, y)
    os.mknod("/static/{}".format(filename))
    return filename
