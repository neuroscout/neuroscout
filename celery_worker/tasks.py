from app import celery_app
from celery.utils.log import get_task_logger

from neuroscout_cli.workflows import fmri_firstlevel
logger = get_task_logger(__name__)

@celery_app.task(name='workflow.compile')
def validate(analysis_json, bids_path):
    # Set optional args to None
    args = {k:None for k in ['-i', '<out_dir>', '-w',
                             'make', 'run', '-c']}
    args.update({'-b' : bids_path, '<bundle>': analysis_json, '--jobs' : 1,
                 '--disable-datalad' : True})

    fmri_firstlevel.FirstLevel(args)
