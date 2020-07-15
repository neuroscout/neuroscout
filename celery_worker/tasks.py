from app import flask_app, celery_app, cache

import neuroscout.tasks.report as report
import neuroscout.tasks.upload as upload


@celery_app.task(name='workflow.compile')
def compile(hash_id, run_ids, build):
    return report.compile(flask_app, hash_id, run_ids, build)


@celery_app.task(name='workflow.generate_report')
def generate_report(hash_id, report_id):
    return report.generate_report(
        flask_app, hash_id, report_id)


@celery_app.task(name='neurovault.upload')
def upload_neurovault(file_id, n_subjects):
    return upload.upload_neurovault(flask_app, file_id, n_subjects)


@celery_app.task(name='collection.upload')
def upload_collection(
        filenames, runs, dataset_id, collection_id, descriptions):
    return upload.upload_collection(flask_app, filenames, runs, dataset_id,
                                    collection_id, descriptions, cache)
