from app import flask_app, celery_app, cache

import neuroscout.tasks.report as report
import neuroscout.tasks.upload as upload


@celery_app.task(name='workflow.compile')
def compile(hash_id, run_ids, build):
    return report.compile(flask_app, hash_id, run_ids, build)


@celery_app.task(name='workflow.generate_report')
def generate_report(hash_id, report_id, run_ids, sampling_rate, scale):
    return report.generate_report(
        flask_app, hash_id, report_id, run_ids, sampling_rate, scale)


@celery_app.task(name='neurovault.upload')
def upload_neurovault(img_tarball, hash_id, upload_id, timestamp, n_subjects):
    return upload.upload_neurovault(flask_app, img_tarball, hash_id,
                                    upload_id, timestamp, n_subjects)


@celery_app.task(name='collection.upload')
def upload_collection(
        filenames, runs, dataset_id, collection_id, descriptions):
    return upload.upload_collection(flask_app, filenames, runs, dataset_id,
                                    collection_id, descriptions, cache)
