from flask_apispec import doc, use_kwargs, MethodResource, marshal_with
from flask import current_app
from ...models import Report, NeurovaultCollection
from ...database import db
from ...worker import celery_app
import webargs as wa
from marshmallow import fields
from ..utils import owner_required, abort, fetch_analysis
from ...schemas.analysis import (
    ReportSchema, AnalysisCompiledSchema, NeurovaultCollectionSchema)
from ...utils.db import put_record

import datetime
import tempfile
from hashids import Hashids


def _validation_hash(analysis_id):
    """ Create a validation hash for the analysis """
    return Hashids(
        current_app.config['SECONDARY_HASH_SALT'],
        min_length=10).encode(analysis_id)


@doc(tags=['analysis'])
@marshal_with(AnalysisCompiledSchema)
class CompileAnalysisResource(MethodResource):
    @use_kwargs({
        'build': wa.fields.Boolean(
            description='Build Analysis object')
        }, locations=['query'])
    @doc(summary='Compile and lock analysis.')
    @owner_required
    def post(self, analysis, build=False):
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
    'run_id': wa.fields.DelimitedList(fields.Int(),
                                      description='Run id(s).'),
    'sampling_rate': wa.fields.Number(description='Sampling rate in Hz'),
    'scale': wa.fields.Boolean(description='Scale columns for plotting'),
}, locations=['query'])
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
            )
        db.session.add(report)
        db.session.commit()

        task = celery_app.send_task(
            'workflow.generate_report',
            args=[analysis.hash_id,
                  report.id,
                  run_id,
                  sampling_rate,
                  scale])
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


# Use current_app
# file_plugin = MarshmallowPlugin()
#
#
# @file_plugin.map_to_openapi_type('file', None)
class FileField(wa.fields.Raw):
    pass


@doc(tags=['analysis'])
class AnalysisUploadResource(MethodResource):
    @doc(summary='Upload fitlins analysis tarball.',
         consumes=['multipart/form-data', 'application/x-www-form-urlencoded'])
    @marshal_with(NeurovaultCollectionSchema)
    @use_kwargs({
        "tarball": FileField(required=True),
        "validation_hash": wa.fields.Str(required=True),
        "force": wa.fields.Bool(),
        "n_subjects": wa.fields.Number(description='Number of subjects'),
        }, locations=["files", "form"])
    @fetch_analysis
    def post(self, analysis, tarball, validation_hash, n_subjects=None,
             force=False):
        # Check hash_id
        if validation_hash != _validation_hash(analysis.id):
            abort(422, "Invalid validation hash.")

        with tempfile.NamedTemporaryFile(
          suffix='_{}.tar.gz'.format(analysis.hash_id),
          dir='/file-data/uploads', delete=False) as f:
            tarball.save(f)

        timestamp = datetime.datetime.utcnow()

        # Create new upload
        upload = NeurovaultCollection(
            analysis_id=analysis.hash_id,
            uploaded_at=timestamp
            )
        db.session.add(upload)
        db.session.commit()

        task = celery_app.send_task(
            'neurovault.upload',
            args=[f.name,
                  analysis.hash_id,
                  upload.id,
                  timestamp if force else None,
                  n_subjects
                  ])

        upload.task_id = task.id
        db.session.commit()

        return upload

    @marshal_with(NeurovaultCollectionSchema(many=True))
    @doc(summary='Get uploads for analyses.')
    @fetch_analysis
    def get(self, analysis):
        return NeurovaultCollection.query.filter_by(
            analysis_id=analysis.hash_id)
