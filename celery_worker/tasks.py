import time
from app import celery_app
import os

@celery_app.task(name='workflow.create')
def create(x):
    time.sleep(10) # lets sleep for a while before doing the gigantic addition task!
    filename = "workflow_{}.py".format(x)
    try:
        os.mknod("/static/{}".format(filename))
    except:
        pass
    return filename
