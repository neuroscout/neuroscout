from flask import send_file, current_app
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from ...models import Analysis, Report
from ...database import db
from ...core import cache
from os.path import exists
import datetime
from webargs import fields
import json
import requests

from ...utils.db import put_record, delete_analysis
from .bib import format_bibliography, find_predictor_citation, _flatten
from ..utils import owner_required, auth_required, fetch_analysis, abort
from ..predictor import get_predictors
from ...schemas.analysis import (
    AnalysisSchema, AnalysisFullSchema,
    AnalysisResourcesSchema, BibliographySchema)


@doc(tags=['analysis'])
@marshal_with(AnalysisSchema)
class AnalysisMethodResource(MethodResource):
    pass


class AnalysisRootResource(AnalysisMethodResource):
    """" Resource for root address """
    @marshal_with(AnalysisSchema(
        many=True,
        only=['hash_id', 'name', 'description', 'status',
              'dataset_id', 'modified_at', 'user']))
    @doc(summary='Returns list of public analyses.')
    @use_kwargs({
        'name': fields.DelimitedList(
            fields.Str(), description="Analysis name(s)"),
        'dataset_id': fields.DelimitedList(
            fields.Number(), description="Dataset id(s)")
        }, location='query')
    def get(self, **kwargs):
        query = Analysis.query.filter_by(private=False, status='PASSED')
        for param in kwargs:
            query = query.filter(
                getattr(Analysis, param).in_(kwargs[param]))

        return query

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
        kwargs['modified_at'] = datetime.datetime.utcnow()
        if analysis.locked is True:
            abort(422, "Analysis is locked. It cannot be edited.")
        if analysis.status not in ['DRAFT', 'FAILED']:
            excep = ['private', 'description', 'name']
            kwargs = {k: v for k, v in kwargs.items() if k in excep}
        if not kwargs:
            abort(422, "Analysis is not editable. Try cloning it.")
        return put_record(kwargs, analysis), 200

    @doc(summary='Delete analysis.')
    @owner_required
    def delete(self, analysis):
        if analysis.status not in ['DRAFT', 'FAILED'] or analysis.locked:
            abort(422, "Analysis not editable, cannot delete.")
            
        delete_analysis(analysis)

        return {'message': 'deleted!'}, 200


class AnalysisFillResource(AnalysisMethodResource):
    @use_kwargs({
        'partial': fields.Boolean(
            description='Attempt partial fill if complete is not possible.',
            missing=True),
        'dryrun': fields.Boolean(
            description="Don't commit autofill results to database")
        }, location='query')
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
            if 'task' in input:
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


class BibliographyResource(MethodResource):
    @doc(tags=['analysis'], summary='Get analysis bibliography')
    @marshal_with(BibliographySchema)
    @fetch_analysis
    def get(self, analysis):
        """ Searches for references for the core tools, dataset and extractors
        used in this analysis. For extractors, individual features can be
        coded as the second-level key in the Bibliography. Otherwise,
        for all other matches, .* is used to denote that all entries match. """
        bib = json.load(open(current_app.config['BIBLIOGRAPHY']))

        neuroscout = [bib['neuroscout']['.*']]

        tools = [b['.*'] for k, b in bib.items()
                 if k in [
                     'nipype', 'fitlins', 'fmriprep', 'pybids', 'pliers']]
        all_csl_json = tools.copy()

        dataset_entry = bib.get(analysis.dataset.name, [])
        data = []
        if dataset_entry:
            data = [dataset_entry['.*']]
            all_csl_json += data

        extraction = [bib['pliers']['.*']]
        # Search for Predictor citations
        extraction += [find_predictor_citation(p, bib)
                       for p in analysis.predictors]
        all_csl_json += extraction

        resp = {
            'neuroscout': format_bibliography(neuroscout),
            'supporting': format_bibliography(tools),
            'data': format_bibliography(data),
            'extraction': format_bibliography(extraction),
            'csl_json': _flatten(all_csl_json)
        }

        return resp


class ImageVersionResource(MethodResource):
    @doc(tags=['analysis'],
         summary='Get latest version of neuroscout cli docker image')
    @cache.cached(60 * 60)
    def get(self):
        url = "https://hub.docker.com/v2/repositories/neuroscout/neuroscout-cli/tags"
        req = requests.get(url)
        try:
            req = req.json()
        except ValueError:
            return {}

        if 'results' in req:
            for res in req['results']:
                if ('version' in res['name']):
                    return {'version': res['name']}

        return {}
