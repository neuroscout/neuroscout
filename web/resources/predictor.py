from marshmallow import Schema, fields
import webargs as wa
from flask_apispec import MethodResource, marshal_with, use_kwargs

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
	name = fields.Str(dump_only=True)
	description = fields.Str(dump_only=True)
	ef_id = fields.Int(dump_only=True)
	predictor_events = fields.Nested(PredictorEventSchema, many=True, only='id')


class PredictorResource(MethodResource):
    @marshal_with(PredictorSchema)
    def get(self, predictor_id):
    	""" Access a predictor by id """
    	return Predictor.query.filter_by(id=predictor_id).first_or_404()

class PredictorListResource(MethodResource):
    @marshal_with(PredictorSchema(many=True))
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(fields.Int()),
        'name': wa.fields.DelimitedList(fields.Str()),
    })
    def get(self, **kwargs):
        """ List of extracted predictors """
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
