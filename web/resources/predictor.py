from marshmallow import Schema, fields
import webargs as wa
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc

from models import Predictor, PredictorEvent


class PredictorEventSchema(Schema):
    id = fields.Str(dump_only=True)
    onset = fields.Number(dump_only=True)
    duration = fields.Number(dump_only=True)
    value = fields.Number(dump_only=True)
    run_id = fields.Int(dump_only=True)
    predictor_id = fields.Int(dump_only=True)

class PredictorSchema(Schema):
	id = fields.Str(dump_only=True)
	name = fields.Str(dump_only=True, description="Predictor name.")
	description = fields.Str(dump_only=True)
	ef_id = fields.Int(dump_only=True,
                    description="If predictor was generated, id of linked extractor feature.")
	predictor_events = fields.Nested(PredictorEventSchema, many=True, only='id',
                                  description="Nested predictor event id(s).")


class PredictorResource(MethodResource):
    @doc(tags=['predictor'], summary='Get predictor by id.')
    @marshal_with(PredictorSchema)
    def get(self, predictor_id):
        return Predictor.query.filter_by(id=predictor_id).first_or_404()

class PredictorListResource(MethodResource):
    @doc(tags=['predictor'], summary='Get list of predictors.',)
    @marshal_with(PredictorSchema(many=True))
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(fields.Int(),
                                          description="Run id(s)"),
        'name': wa.fields.DelimitedList(fields.Str(),
                                        description="Predictor name(s)"),
    }, locations=['query'], inherit=True)
    def get(self, **kwargs):
        try:
            run_id = kwargs.pop('run_id')
        except KeyError:
            run_id = None

        query = Predictor.query
        for param in kwargs:
        	query = query.filter(getattr(Predictor, param).in_(kwargs[param]))

        if run_id:
        	query = query.join('predictor_events').filter(
        		PredictorEvent.run_id.in_(run_id))

        return query.all()
