from app import flask_app, celery_app

import neuroscout.tasks.report as report
import neuroscout.tasks.upload as upload


@celery_app.task('workflow.compile')
def compile(hash_id, run_ids, build):
    report.compile(flask_app, hash_id, run_ids, build)


@celery_app.task('workflow.generate_report')
def generate_report(hash_id, report_id, run_ids, sampling_rate, scale):
    report.report(flask_app, hash_id, report_id, run_ids, sampling_rate, scale)


@celery_app.task('neurovault.upload')
def upload_neurovault(img_tarball, hash_id, upload_id, timestamp, n_subjects):
    upload.upload_neurovault(flask_app, img_tarball, hash_id,
                             upload_id, timestamp, n_subjects)


@celery_app.task('collection.upload')
def upload_collection(filenames, runs, dataset_id, collection_id):
    upload.upload_collection(flask_app, filenames, runs,
                             dataset_id, collection_id)
