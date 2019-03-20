from flask_apispec import doc, use_kwargs, MethodResource, marshal_with
from database import db
from flask import current_app
from models import PredictorEvent, Report, NeurovaultCollection
from worker import celery_app
import webargs as wa
from marshmallow import fields
from ..utils import owner_required, abort, fetch_analysis
from ..predictor import dump_pe
from .schemas import (AnalysisFullSchema, AnalysisResourcesSchema,
                      ReportSchema, AnalysisCompiledSchema,
                      NeurovaultCollectionSchema)
import celery.states as states
from utils import put_record
import datetime
import tempfile
from hashids import Hashids
from core import file_plugin


def jsonify_analysis(analysis, run_id=None):
    """" Serialize to JSON analysis's predictor events
    Queries PredictorEvents to get all events for all runs and predictors. """

    analysis_json = AnalysisFullSchema().dump(analysis)[0]
    pred_ids = [p['id'] for p in analysis_json['predictors']]
    all_runs = [r['id'] for r in analysis_json['runs']]

    if run_id is None:
        run_id = all_runs
    if not set(run_id) <= set(all_runs):
        raise ValueError("Incorrect run id specified")

    pes = PredictorEvent.query.filter(
        (PredictorEvent.predictor_id.in_(pred_ids)) &
        (PredictorEvent.run_id.in_(run_id)))

    return analysis_json, dump_pe(pes)


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
        put_record(
            {'status': 'SUBMITTING',
             'submitted_at': datetime.datetime.utcnow()},
            analysis)

        validation_hash = Hashids(
            current_app.config['SECONDARY_HASH_SALT'],
            min_length=10).encode(analysis.id)

        try:
            task = celery_app.send_task(
                'workflow.compile',
                args=[*jsonify_analysis(analysis),
                      AnalysisResourcesSchema().dump(analysis)[0],
                      analysis.dataset.local_path, None, validation_hash,
                      build]
                )
        except:
            put_record(
                {'status': 'FAILED',
                 'compile_traceback': "Submitting failed. "
                 "Perhaps analysis is too large?"},
                analysis)

        put_record({'status': 'PENDING', 'compile_task_id': task.id}, analysis)

        return analysis

    @doc(summary='Check if analysis compilation status.')
    @fetch_analysis
    def get(self, analysis):
        return analysis


@marshal_with(ReportSchema)
@use_kwargs({
    'run_id': wa.fields.DelimitedList(fields.Int(),
                                      description='Run id(s).')
}, locations=['query'])
@doc(tags=['analysis'])
class ReportResource(MethodResource):
    @doc(summary='Generate analysis reports.')
    @fetch_analysis
    def post(self, analysis, run_id=None):
        # Submit report generation
        analysis_json, pes_json = jsonify_analysis(analysis, run_id=run_id)

        task = celery_app.send_task(
            'workflow.generate_report',
            args=[analysis_json, pes_json,
                  analysis.dataset.local_path, run_id,
                  current_app.config['SERVER_NAME']])

        # Create new Report
        report = Report(
            analysis_id=analysis.hash_id,
            runs=run_id,
            task_id=task.id
            )
        db.session.add(report)
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

        if report.status == 'PENDING':
            res = celery_app.AsyncResult(report.task_id)
            if res.state == states.FAILURE:
                put_record(
                    {'status': 'FAILED', 'traceback': res.traceback}, report)
            elif res.state == states.SUCCESS:
                put_record(
                    {'status': 'OK', 'result': res.result}, report)

        return report


@file_plugin.map_to_openapi_type('file', None)
class FileField(wa.fields.Raw):
    pass


@doc(tags=['analysis'])
class AnalysisUploadResource(MethodResource):
    @doc(summary='Upload fitlins analysis tarball.',
         consumes=['multipart/form-dat', 'application/x-www-form-urlencoded'])
    @marshal_with(NeurovaultCollectionSchema)
    @use_kwargs({
        "tarball": FileField(required=True),
        "validation_hash": wa.fields.Str(required=True),
        "force": wa.fields.Bool()},
                locations=["files", "form"])
    @fetch_analysis
    def post(self, analysis, tarball, validation_hash, force=False):
        # Check hash_id
        correct = Hashids(current_app.config['SECONDARY_HASH_SALT'],
                          min_length=10).encode(analysis.id)

        if correct != validation_hash:
            abort(422, "Invalid validation hash.")

        with tempfile.NamedTemporaryFile(
          suffix='_{}.tar.gz'.format(analysis.hash_id),
          dir='/file-data/uploads', delete=False) as f:
            tarball.save(f)

        timestamp = datetime.datetime.utcnow()

        task = celery_app.send_task(
            'neurovault.upload',
            args=[f.name,
                  analysis.hash_id,
                  current_app.config['NEUROVAULT_ACCESS_TOKEN'],
                  timestamp if force else None
                  ])

        # Create new upload
        upload = NeurovaultCollection(
            analysis_id=analysis.hash_id,
            task_id=task.id,
            uploaded_at=timestamp
            )
        db.session.add(upload)
        db.session.commit()

        return upload

    @marshal_with(NeurovaultCollectionSchema(many=True))
    @doc(summary='Get uploads for analyses.')
    @fetch_analysis
    def get(self, analysis):
        uploads = NeurovaultCollection.query.filter_by(
            analysis_id=analysis.hash_id)

        # Update upload statuses
        for up in uploads:
            if up.status == 'PENDING':
                res = celery_app.AsyncResult(up.task_id)
                if res.state == states.FAILURE:
                    put_record(
                        {'status': 'FAILED', 'traceback': res.traceback}, up)
                elif res.state == states.SUCCESS:
                    put_record(
                        {'status': 'OK',
                         'collection_id': res.result['collection_id']}, up)

        return uploads
