from flask import send_file
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from database import db
from models import Analysis, Report
from os.path import exists
import datetime
import webargs as wa

from utils.db import put_record
from ..utils import owner_required, auth_required, fetch_analysis, abort
from ..predictor import get_predictors
from .schemas import (AnalysisSchema, AnalysisFullSchema,
                      AnalysisResourcesSchema)


@doc(tags=['analysis'])
@marshal_with(AnalysisSchema)
class AnalysisMethodResource(MethodResource):
    pass


class AnalysisRootResource(AnalysisMethodResource):
    """" Resource for root address """
    @marshal_with(AnalysisSchema(many=True))
    @doc(summary='Returns list of public analyses.')
    def get(self):
        return Analysis.query.filter_by(private=False, status='PASSED').all()

    @use_kwargs(AnalysisSchema)
    @doc(summary='Add new analysis!')
    @auth_required
    def post(self, **kwargs):
        new = Analysis(user_id=current_identity.id, **kwargs)
        db.session.add(new)
        db.session.commit()
        return new


class AnalysisResource(AnalysisMethodResource):
    @doc(summary='Get analysis by id.')
    @fetch_analysis
    def get(self, analysis):
        return analysis

    @doc(summary='Edit analysis.')
    @use_kwargs(AnalysisSchema)
    @owner_required
    def put(self, analysis, **kwargs):
        if analysis.locked is True:
            abort(422, "Analysis is locked. It cannot be edited.")
        if analysis.status not in ['DRAFT', 'FAILED']:
            excep = ['private', 'description']
            kwargs = {k: v for k, v in kwargs.items() if k in excep}
        if not kwargs:
            abort(422, "Analysis is not editable. Try cloning it.")
        kwargs['modified_at'] = datetime.datetime.utcnow()
        return put_record(kwargs, analysis)

    @doc(summary='Delete analysis.')
    @owner_required
    def delete(self, analysis):
        if analysis.status not in ['DRAFT', 'FAILED'] or analysis.locked:
                abort(422, "Analysis not editable, cannot delete.")

        # Delete reports
        Report.query.filter_by(analysis_id=analysis.hash_id).delete()

        db.session.delete(analysis)
        db.session.commit()

        return {'message': 'deleted!'}


class AnalysisFillResource(AnalysisMethodResource):
    @use_kwargs({
        'partial': wa.fields.Boolean(
            description='Attempt partial fill if complete fill is not possible.')
        }, locations=['query'])
    @doc(summary='Auto fill fields from model.')
    @owner_required
    def post(self, analysis, partial=False):
        if analysis.status not in ['DRAFT', 'FAILED'] or analysis.locked:
                abort(422, "Analysis not editable.")

        fields = {}

        if not analysis.runs:
            #  Set to all runs in dataset
            fields['runs'] = analysis.dataset.runs.all()
            fields['model'] = analysis.model
            fields['model'].pop("Input")
        if not analysis.predictors:
            # Look in model to see if there are predictor names
            try:
                names = analysis.model['Steps'][0]['Model']['X']
            except (KeyError, TypeError):
                names = None

            if names is not None:
                runs = fields['runs'] if 'runs' in fields else analysis.runs
                if 'runs' in fields:
                    runs = fields['runs']
                    
                predictors = get_predictors(
                    name=names, run_id=[r.id for r in runs])

                if len(predictors) == len(names):
                    fields['predictors'] = predictors
                elif len(predictors) < len(names) and partial is True:
                    new_names = [p.name for p in predictors]
                    if 'model' not in fields:
                        fields['model'] = analysis.model
                    fields['model']['Steps'][0]['Model']['X'] = new_names
                    fields['predictors'] = predictors

        if fields:
            fields['modified_at'] = datetime.datetime.utcnow()
            return put_record(fields, analysis)
        else:
            return analysis


class CloneAnalysisResource(AnalysisMethodResource):
    @doc(summary='Clone analysis.')
    @auth_required
    @fetch_analysis
    def post(self, analysis):
        if analysis.status != 'PASSED':
            abort(422, "Only passed analyses can be cloned.")

        cloned = analysis.clone(current_identity)
        db.session.add(cloned)
        db.session.commit()
        return cloned


class AnalysisFullResource(AnalysisMethodResource):
    @marshal_with(AnalysisFullSchema)
    @doc(summary='Get analysis (including nested fields).')
    @fetch_analysis
    def get(self, analysis):
        return analysis


class AnalysisResourcesResource(AnalysisMethodResource):
    @marshal_with(AnalysisResourcesSchema)
    @doc(summary='Get analysis resources.')
    @fetch_analysis
    def get(self, analysis):
        return analysis


class AnalysisBundleResource(MethodResource):
    @doc(tags=['analysis'], summary='Get analysis tarball bundle.',
         responses={"200": {
             "description": "tarball, including analysis, resources, events.",
             "type": "application/x-tar"}})
    @fetch_analysis
    def get(self, analysis):
        if (analysis.status != "PASSED" or analysis.bundle_path is None or
           not exists(analysis.bundle_path)):
            msg = "Analysis bundle not available. Try compiling."
            abort(404, msg)
        return send_file(analysis.bundle_path, as_attachment=True)
