from flask import send_file, current_app
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from database import db
from models import Analysis, Report
from os.path import exists
import datetime
import webargs as wa
import json

from utils.db import put_record
from ..utils import owner_required, auth_required, fetch_analysis, abort
from ..predictor import get_predictors
from .schemas import (AnalysisSchema, AnalysisFullSchema,
                      AnalysisResourcesSchema, BibliographySchema)

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
        return new, 200


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
            excep = ['private', 'description', 'name']
            kwargs = {k: v for k, v in kwargs.items() if k in excep}
        if not kwargs:
            abort(422, "Analysis is not editable. Try cloning it.")
        kwargs['modified_at'] = datetime.datetime.utcnow()
        return put_record(kwargs, analysis), 200

    @doc(summary='Delete analysis.')
    @owner_required
    def delete(self, analysis):
        if analysis.status not in ['DRAFT', 'FAILED'] or analysis.locked:
            abort(422, "Analysis not editable, cannot delete.")

        analysis.runs = []

        # Delete reports
        Report.query.filter_by(analysis_id=analysis.hash_id).delete()

        db.session.delete(analysis)
        db.session.commit()

        return {'message': 'deleted!'}, 200


class AnalysisFillResource(AnalysisMethodResource):
    @use_kwargs({
        'partial': wa.fields.Boolean(
            description='Attempt partial fill if complete is not possible.',
            missing=True),
        'dryrun': wa.fields.Boolean(
            description="Don't commit autofill results to database")
        }, locations=['query'])
    @doc(summary='Auto fill fields from model.')
    @owner_required
    def post(self, analysis, partial=True, dryrun=False):
        if analysis.status not in ['DRAFT', 'FAILED'] or analysis.locked:
            abort(422, "Analysis not editable.")

        fields = {}

        if not analysis.runs:
            #  Set to all runs in dataset
            fields['runs'] = analysis.dataset.runs
            fields['model'] = analysis.model

            input = {k: list(set(getattr(r, k)
                                 for r in fields['runs']
                                 if getattr(r, k) is not None))
                     for k in ['subject', 'number', 'task', 'session']}
            input['run'] = input.pop('number')
            input['task'] = [t.name for t in input['task']]
            fields['model']['Input'] = {
                k.capitalize(): v for k, v in input.items() if v}

        if not analysis.predictors:
            # Look in model to see if there are predictor names
            try:
                names = analysis.model['Steps'][0]['Model']['X']
            except (KeyError, TypeError):
                names = None

            if names:
                runs = fields['runs'] if 'runs' in fields else analysis.runs

                predictors = get_predictors(
                    name=names, run_id=[r.id for r in runs])

                if len(predictors) == len(names):
                    fields['predictors'] = predictors
                elif len(predictors) < len(names):
                    if partial:
                        fields['predictors'] = predictors

                        new_names = [p.name for p in predictors]
                        missing = set(names) - set(new_names)

                        if 'model' not in fields:
                            fields['model'] = analysis.model
                        fields['model']['Steps'][0]['Model']['X'] = new_names

                        # If any transformations use missing predictors, drop
                        if any([t for t in
                                fields['model']['Steps'][0]['Transformations']
                                if missing.intersection(t['Input'])]):
                            fields['model']['Steps'][0]['Transformations'] = []
                            fields['model']['Steps'][0]['Contrasts'] = []

                        # If any contrasts use missing predictors, drop all
                        if any([t for t in
                                fields['model']['Steps'][0]['Contrasts']
                                if missing.intersection(t['ConditionList'])]):
                            fields['model']['Steps'][0]['Contrasts'] = []

        if fields:
            fields['modified_at'] = datetime.datetime.utcnow()
            return put_record(fields, analysis, commit=(not dryrun))
        else:
            return analysis, 200


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
        return cloned, 200


class AnalysisFullResource(AnalysisMethodResource):
    @marshal_with(AnalysisFullSchema)
    @doc(summary='Get analysis (including nested fields).')
    @fetch_analysis
    def get(self, analysis):
        return analysis, 200


class AnalysisResourcesResource(AnalysisMethodResource):
    @marshal_with(AnalysisResourcesSchema)
    @doc(summary='Get analysis resources.')
    @fetch_analysis
    def get(self, analysis):
        return analysis, 200


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


def _flatten(li):
    return [item for sublist in li for item in sublist]


class BibliographyResource(MethodResource):
    @doc(tags=['analysis'], summary='Get analysis bibliography')
    @marshal_with(BibliographySchema)
    @fetch_analysis
    def get(self, analysis):
        bib = json.load(open(current_app.config['BIBLIOGRAPHY']))
        CORE = ['nipype', 'neuroscout', 'fitlins', 'nipype']

        resp = {
            'tools': _flatten([b for k, b in bib.items() if k in CORE]),
            'data': [],
            'extractors': []
        }

        return resp
