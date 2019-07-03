import webargs as wa
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from ..models import Predictor, PredictorEvent, PredictorRun
from ..database import db
from .utils import first_or_404
from sqlalchemy import func
from ..core import cache
from ..utils.db import dump_pe
from ..schemas.predictor import PredictorSchema


class PredictorResource(MethodResource):
    @doc(tags=['predictors'], summary='Get predictor by id.')
    @marshal_with(PredictorSchema)
    def get(self, predictor_id, **kwargs):
        return first_or_404(Predictor.query.filter_by(id=predictor_id))


def get_predictors(newest=True, **kwargs):
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

    # Only display active predictors
    return query.filter_by(active=True).all()


class PredictorListResource(MethodResource):
    @doc(tags=['predictors'], summary='Get list of predictors.',)
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(
            wa.fields.Int(), description="Run id(s). Warning, slow query."),
        'name': wa.fields.DelimitedList(wa.fields.Str(),
                                        description="Predictor name(s)"),
        'newest': wa.fields.Boolean(
            missing=True,
            description="Return only newest Predictor by name")
        },
        locations=['query'])
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    @marshal_with(PredictorSchema(many=True))
    def get(self, **kwargs):
        newest = kwargs.pop('newest')
        return get_predictors(newest=newest, **kwargs)


class PredictorEventListResource(MethodResource):
    @doc(tags=['predictors'], summary='Get events for predictor(s)',)
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(
            wa.fields.Int(),
            description="Run id(s)"),
        'predictor_id': wa.fields.DelimitedList(
            wa.fields.Int(),
            description="Predictor id(s)"),
    }, locations=['query'])
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    def get(self, **kwargs):
        query = PredictorEvent.query
        for param in kwargs:
            query = query.filter(
                getattr(PredictorEvent, param).in_(kwargs[param]))
        return dump_pe(query)


class PredictorCreateResource(MethodResource):
    @doc(tags=['predictors'], summary='Create a new predictor')
    def post(self, **kwargs):
        return {}
