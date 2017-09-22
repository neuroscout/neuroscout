from app import celery_app
from celery.utils.log import get_task_logger

import sys
sys.path.insert(1, '/neuroscout/workflow/')
from importlib import import_module
fmri = import_module('fmri_bids_firstlevel')

logger = get_task_logger(__name__)

@celery_app.task(name='workflow.compile')
def validate(analysis_json, bids_path):
    # Set optional args to None
    args = {k:None for k in ['-i', '<out_dir>', '-w',
                             'make', 'run', '-c']}
    args.update({'-b' : bids_path, '<bundle>': analysis_json, '--jobs' : 1,
                 '--disable-datalad' : True})

    fmri.FirstLevel(args)
