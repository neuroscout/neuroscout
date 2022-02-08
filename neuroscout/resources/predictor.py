from webargs import fields
import tempfile
import json
from marshmallow import INCLUDE, Schema
from sqlalchemy import func
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from flask import current_app
from pathlib import Path
from .utils import abort, auth_required, first_or_404
from ..models import (
    Predictor, PredictorRun, PredictorCollection, Task)
from ..database import db
from ..core import cache
from ..schemas.predictor import (
    PredictorSchema, PredictorEventSchema, PredictorCollectionSchema)
from ..schemas.analysis import AnalysisSchema
from ..schemas.dataset import DatasetSchema
from ..api_spec import FileField
from ..worker import celery_app
from ..utils.db import dump_predictor_events


class PredictorResource(MethodResource):
    @doc(tags=['predictors'], summary='Get predictor by id.')
    @marshal_with(PredictorSchema)
    def get(self, predictor_id, **kwargs):
        return first_or_404(Predictor.query.filter_by(id=predictor_id))


def get_predictors(newest=True, active=True, user=None, **kwargs):
    """ Helper function for querying newest predictors """
    if newest:
        predictor_ids = db.session.query(
            func.max(Predictor.id)).group_by(Predictor.name)
    else:
        predictor_ids = db.session.query(Predictor.id)

    if 'run_id' in kwargs:
        # This following JOIN can be slow
        predictor_ids = predictor_ids.join(PredictorRun).filter(
            PredictorRun.run_id.in_(kwargs.pop('run_id')))

    query = Predictor.query.filter(Predictor.id.in_(predictor_ids))

    for param in kwargs:
        query = query.filter(getattr(Predictor, param).in_(kwargs[param]))

    if active:
        query = query.filter_by(active=active)

    if user is not None:
        query = query.filter_by(private=True).join(
            PredictorCollection).filter_by(user_id=user.id)
    else:
        query = query.filter_by(private=False)

    # Only display active predictors
    return query.all()


class PredictorListResource(MethodResource):
    @doc(tags=['predictors'], summary='Get list of predictors.',)
    @use_kwargs({
        'run_id': fields.DelimitedList(
            fields.Int(), description="Run id(s). Warning, slow query."),
        'name': fields.DelimitedList(
            fields.Str(), description="Predictor name(s)"),
        'active_only': fields.Boolean(
            missing=True,
            description="Return only active Predictors"),
        'newest': fields.Boolean(
            missing=True,
            description="Return only newest Predictor by name")
        },
        location='query')
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    @marshal_with(PredictorSchema(many=True))
    def get(self, **kwargs):
        newest = kwargs.pop('newest')
        active = kwargs.pop('active_only')
        return get_predictors(newest=newest, active=active, **kwargs)


def prepare_upload(collection_name, event_files, runs, dataset_id):
    if len(event_files) != len(runs):
        abort(422, "The length of event_files and runs must be the same.")

    # Assert that list of runs is non overlapping
    flat = [item for sublist in runs for item in sublist]
    if len(set(flat)) != len(flat):
        abort(422, "Runs can only be assigned to a single event file.")

    filenames = []
    for e in event_files:
        with tempfile.NamedTemporaryFile(
          suffix=f'_{collection_name}.tsv',
          dir=str(Path(
              current_app.config['FILE_DIR']) / 'predictor_collections'),
          delete=False) as f:
            e.save(f)
            filenames.append(f.name)

    # Send to Celery task
    # Create new upload
    pc = PredictorCollection(
        collection_name=collection_name,
        user_id=getattr(current_identity, 'id', None)
        )
    db.session.add(pc)
    db.session.commit()

    return pc, filenames


class TaskPredictorsResource(MethodResource):
    @doc(tags=['predictors'], summary='Get list of predictors.',)
    @use_kwargs({
        'active_only': fields.Boolean(
            missing=True,
            description="Return only active Predictors"),
        'newest': fields.Boolean(
            missing=True,
            description="Return only newest Predictor by name")
        },
        location='query')
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    @marshal_with(PredictorSchema(many=True))
    def get(self, task_id, **kwargs):
        newest = kwargs.pop('newest')
        active = kwargs.pop('active_only')
        task = first_or_404(Task.query.filter_by(id=task_id))
        run_id = [r.id for r in task.runs]
        return get_predictors(newest=newest, active=active,
                              run_id=run_id, **kwargs)


class FormSchema(Schema):
    collection_name = fields.Str(
        required=True, description="Name of collection")
    runs = fields.List(
        fields.DelimitedList(fields.Int()),
        required=True
        )
    dataset_id = fields.Int(required=True)
    descriptions = fields.Str(description='Column descriptions')

    class Meta:
        unknown = INCLUDE


class FileSchema(Schema):
    event_files = fields.List(
        FileField(), required=True,
        description="TSV files with additional Predictors to be created.\
        Required columns: onset, duration, any number of columns\
        with values for new Predictors."
        )

    class Meta:
        unknown = INCLUDE


@doc(tags=['predictors'])
class PredictorCollectionCreateResource(MethodResource):
    @doc(summary='Create a custom Predictor using uploaded annotations.',
         consumes=['multipart/form-data', 'application/x-www-form-urlencoded'])
    @marshal_with(PredictorCollectionSchema)
    @use_kwargs(FormSchema, location="form")
    @use_kwargs(FileSchema, location="files")
    @auth_required
    def post(self, collection_name, event_files, runs, dataset_id,
             descriptions=None):
        if descriptions is not None:
            descriptions = json.loads(descriptions)
        pc, filenames = prepare_upload(
            collection_name, event_files, runs, dataset_id)

        task = celery_app.send_task(
            'collection.upload',
            args=[filenames,
                  runs,
                  dataset_id,
                  pc.id,
                  descriptions
                  ])

        pc.task_id = task.id
        db.session.commit()
        return pc


@doc(tags=['predictors'])
class PredictorCollectionResource(MethodResource):
    @doc(summary='Get predictor collection by id.')
    @marshal_with(PredictorCollectionSchema)
    def get(self, pc_id, **kwargs):
        return first_or_404(
            PredictorCollection.query.filter_by(id=pc_id))


class PredictorEventListResource(MethodResource):
    @doc(tags=['predictors'], summary='Get events for predictor(s)',)
    @marshal_with(PredictorEventSchema(many=True))
    @use_kwargs({
        'run_id': fields.DelimitedList(
            fields.Int(),
            description="Run id(s)"),
        'predictor_id': fields.DelimitedList(
            fields.Int(),
            description="Predictor id(s)",
            required=True),
        'stimulus_timing': fields.Boolean(
            missing=False,
            description="Return stimulus timing and information")
        }, location='query')
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    def get(self, predictor_id, run_id=None, stimulus_timing=False):
        return dump_predictor_events(
            predictor_id, run_id, stimulus_timing=stimulus_timing)

''' Get the ExtractedFeature for the predictor, get all ExtractedFeatures
    with same feature_name and extractor, get all dataset_ids from Predictor
    table that use any of those ef_ids.
'''
class PredictorRelatedResource(MethodResource):
    @use_kwargs({
        'predictor_id': fields.DelimitedList(
            fields.Int(),
            description="Predictor id(s)",
            required=True),
    })
    def get(self, predictor_id):
        predictor = Predictor.query.get(id=predictor_id)
        analyses = []
        for a in [x.analysis for x in Predictor.query.filter_by(name=predcitor.name).all()]:
            analyses.extend(a)
        datasets = [x.dataset for x in Predictor.query.filter_by(name='rms').distinct('dataset_id').all()]
        aSchema = AnalysisSchema(many=True)
        dSchema = DatasetSchema(many=True)
        return {analyses: aSchema.dump(analyses), datasets: dSchema.dump(datasets)}
        
