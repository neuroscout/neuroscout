import datetime
from hashids import Hashids
from webargs import fields
from marshmallow import INCLUDE, Schema
from flask_apispec import doc, use_kwargs, MethodResource, marshal_with
from flask import current_app
from pathlib import Path
from pynv import Client

from ...models import Report, NeurovaultCollection, NeurovaultFileUpload
from ...database import db
from ...worker import celery_app
from ...schemas.analysis import (
    ReportSchema, AnalysisCompiledSchema, NeurovaultCollectionSchemaStatus)
from ...utils.db import put_record
from ..utils import owner_required, abort, fetch_analysis
from ...api_spec import FileField


def _validation_hash(analysis_id):
    """ Create a validation hash for the analysis """
    return Hashids(
        current_app.config['SECONDARY_HASH_SALT'],
        min_length=10).encode(analysis_id)


@doc(tags=['analysis'])
@marshal_with(AnalysisCompiledSchema)
class CompileAnalysisResource(MethodResource):
    @use_kwargs({
        'build': fields.Boolean(
            description='Build Analysis object')
        }, location='query')
    @doc(summary='Compile and lock analysis.')
    @owner_required
    def post(self, analysis, build=False):
        if analysis.name is None:
            abort(404, "Analysis must be given a name before compilation.")
        try:
            task = celery_app.send_task(
                'workflow.compile',
                args=[analysis.hash_id, None, build]
                )
            put_record(
                {'status': 'PENDING',
                 'traceback': '',
                 'compile_task_id': task.id}, analysis)

        except Exception as e:
            put_record(
                {'status': 'FAILED',
                 'compile_traceback': str(e)},
                analysis)

        return analysis

    @doc(summary='Check if analysis compilation status.')
    @fetch_analysis
    def get(self, analysis):
        return analysis


@marshal_with(ReportSchema)
@use_kwargs({
    'run_id': fields.DelimitedList(
        fields.Int(), description='Run id(s).'),
    'sampling_rate': fields.Number(description='Sampling rate in Hz'),
    'scale': fields.Boolean(description='Scale columns for plotting'),
}, location='query')
@doc(tags=['analysis'])
class ReportResource(MethodResource):
    @doc(summary='Generate analysis reports.')
    @fetch_analysis
    def post(self, analysis, run_id=None, sampling_rate=None, scale=True):
        # Submit report generation

        # Create new Report
        report = Report(
            analysis_id=analysis.hash_id,
            runs=run_id,
            scale=scale,
            sampling_rate=sampling_rate
            )
        db.session.add(report)
        db.session.commit()

        task = celery_app.send_task(
            'workflow.generate_report',
            args=[analysis.hash_id,
                  report.id
                  ])
        report.task_id = task.id
        db.session.commit()

        return report, 200

    @doc(summary='Get analysis reports.')
    @fetch_analysis
    def get(self, analysis, run_id=None):
        filters = {'analysis_id': analysis.hash_id}
        if run_id is not None:
            filters['runs'] = run_id

        candidate = Report.query.filter_by(**filters)
        if candidate.count() == 0:
            abort(404, "Report not found")

        report = candidate.filter_by(
            generated_at=max(candidate.with_entities('generated_at'))).one()

        if report.generated_at < analysis.modified_at:
            abort(404, "No fresh reports available")

        return report


def _save_file(file, collection_id):
    upload_dir = Path(
        current_app.config['FILE_DIR']) / 'uploads' / str(collection_id)
    path = upload_dir / Path(file.filename).parts[-1]

    file.save(path.open('wb'))
    return str(path)


def _truncate_string(si, max_char):
    if len(si) > max_char:
        middle_point = int(len(si) / 2)
        diff = int((len(si) - max_char) / 2)
        end = middle_point - diff
        si = si[:end]+"..."+si[-end:]
    return si


def _create_collection(
      analysis, cli_version=None, fmriprep_version=None, estimator=None,
      force=False):
    collection_name = f"{analysis.name} - {analysis.hash_id}"
    if force is True:
        timestamp = datetime.datetime.utcnow().strftime(
            '%Y-%m-%d_%H:%M')
        collection_name += f"_{timestamp}"

    collection_name = _truncate_string(collection_name, 195)

    url = f"https://{current_app.config['SERVER_NAME']}"\
          f"/builder/{analysis.hash_id}"
    try:
        api = Client(
            access_token=current_app.config['NEUROVAULT_ACCESS_TOKEN'])
        collection = api.create_collection(
            collection_name,
            description=analysis.description,
            full_dataset_url=url)
    except Exception:
        abort(422, f"Error creating collection named: {collection_name}, "
                   "perhaps one with that name already exists?")

    # Create new NV collection
    upload = NeurovaultCollection(
        analysis_id=analysis.hash_id,
        collection_id=collection['id'],
        cli_version=cli_version,
        fmriprep_version=fmriprep_version,
        estimator=estimator
        )
    db.session.add(upload)
    db.session.commit()

    upload_dir = Path(
        current_app.config['FILE_DIR']) / 'uploads' / str(collection['id'])
    upload_dir.mkdir(exist_ok=True)

    return upload


class NVUploadFormSchema(Schema):
    validation_hash = fields.Str(required=True)
    collection_id = fields.Int()
    force = fields.Bool()
    level = fields.Str()
    n_subjects = fields.Number()
    cli_version = fields.Str()
    fmriprep_version = fields.Str()
    estimator = fields.Str()

    class Meta:
        unknown = INCLUDE


class NVUploadFileSchema(Schema):
    image_file = FileField(required=True)

    class Meta:
        unknown = INCLUDE


@doc(tags=['analysis'])
class AnalysisUploadResource(MethodResource):
    @doc(summary='Upload fitlins analysis results. ',
         consumes=['multipart/form-data', 'application/x-www-form-urlencoded'])
    @marshal_with(NeurovaultCollectionSchemaStatus)
    @use_kwargs(NVUploadFormSchema, location="form")
    @use_kwargs(NVUploadFileSchema, location="files")
    @fetch_analysis
    def post(self, analysis, validation_hash, collection_id=None,
             cli_version=None, fmriprep_version=None, estimator=None,
             image_file=None, level=None, n_subjects=None, force=False):
        if validation_hash != _validation_hash(analysis.id):
            abort(422, "Invalid validation hash.")

        # Create or fetch NeurovaultCollection
        if collection_id is None:
            upload = _create_collection(
                analysis, cli_version, fmriprep_version, estimator, force)
            collection_id = upload.collection_id
        else:
            upload = NeurovaultCollection.query.filter_by(
                collection_id=collection_id).first()
            if upload is None:
                abort(404, 'No record of collection id.')

        # If file, upload
        if image_file is not None:
            if level is None:
                abort(422, "Must provide image level.")

            path = _save_file(image_file, collection_id)
            # Create new file upload task
            file_upload = NeurovaultFileUpload(
                nv_collection_id=upload.id,
                path=path,
                level=level
                )
            db.session.add(file_upload)
            db.session.commit()

            task = celery_app.send_task(
                'neurovault.upload',
                args=[file_upload.id,
                      n_subjects]
                )

            file_upload.task_id = task.id
            db.session.commit()

        return upload

    @marshal_with(NeurovaultCollectionSchemaStatus(many=True))
    @doc(summary='Get uploads for analyses.')
    @fetch_analysis
    def get(self, analysis):
        return NeurovaultCollection.query.filter_by(
            analysis_id=analysis.hash_id)
