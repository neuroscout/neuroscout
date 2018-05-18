from marshmallow import Schema, fields, post_dump
import webargs as wa
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from .utils import first_or_404
from sqlalchemy import func
from ..app import db
from ..models import Predictor, PredictorEvent

class ExtractedFeatureSchema(Schema):
    id = fields.Int(description="Extractor id")
    description = fields.Str(description="Feature description.")
    created_at = fields.Str(description="Extraction timestamp.")

class PredictorSchema(Schema):
    id = fields.Int()
    name = fields.Str(description="Predictor name.")
    description = fields.Str()
    extracted_feature = fields.Nested('ExtractedFeatureSchema', skip_if=None)

    @post_dump
    def remove_null_values(self, data):
        if data.get('extracted_feature', True) is None:
            data.pop('extracted_feature')
        return data

class PredictorSingleSchema(PredictorSchema):
    run_statistics = fields.Nested('PredictorRunSchema', many=True)

class PredictorEventSchema(Schema):
    id = fields.Str()
    onset = fields.Number(description="Onset in seconds.")
    duration = fields.Number(description="Duration in seconds.")
    value = fields.Str(description="Value, or amplitude.")
    run_id = fields.Int()
    predictor_id = fields.Int()

class PredictorRunSchema(Schema):
    run_id = fields.Int()
    mean = fields.Number()
    stdev = fields.Number()

class PredictorResource(MethodResource):
    @doc(tags=['predictors'], summary='Get predictor by id.')
    @marshal_with(PredictorSingleSchema)
    def get(self, predictor_id, **kwargs):
        return first_or_404(Predictor.query.filter_by(id=predictor_id))

class PredictorListResource(MethodResource):
    @doc(tags=['predictors'], summary='Get list of predictors.',)
    @marshal_with(PredictorSchema(many=True))
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(fields.Int(),
                                          description="Run id(s)"),
        'name': wa.fields.DelimitedList(fields.Str(),
                                        description="Predictor name(s)"),
        'newest': wa.fields.Boolean(missing=True,
                    description="Return only newest Predictor by name")
        },
        locations=['query'])
    def get(self, **kwargs):
        if kwargs.pop('newest'):
            predictor_ids = db.session.query(
                func.max(Predictor.id)).group_by(Predictor.name)
        else:
            predictor_ids = db.session.query(Predictor.id)

        if 'run_id' in kwargs:
            run_id = kwargs.pop('run_id')
            predictor_ids = predictor_ids.join(PredictorEvent).filter(
                PredictorEvent.run_id.in_(run_id))

        query = Predictor.query.filter(Predictor.id.in_(predictor_ids))
        for param in kwargs:
            query = query.filter(getattr(Predictor, param).in_(kwargs[param]))


        return query.all()

class PredictorEventListResource(MethodResource):
    @doc(tags=['predictors'], summary='Get events for predictor(s)',)
    @marshal_with(PredictorEventSchema(many=True, exclude=['predictor']))
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(fields.Int(),
                                          description="Run id(s)"),
        'predictor_id': wa.fields.DelimitedList(fields.Int(),
                                        description="Predictor id(s)"),
    }, locations=['query'])
    def get(self, **kwargs):
        query = PredictorEvent.query
        for param in kwargs:
            query = query.filter(getattr(PredictorEvent, param).in_(kwargs[param]))
        return query.all()
