from marshmallow import Schema, fields
import webargs as wa
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from models import Predictor, PredictorEvent
from . import utils

""" Predictors """
class PredictorSchema(Schema):
	id = fields.Str(dump_only=True)
	name = fields.Str(dump_only=True, description="Predictor name.")
	description = fields.Str(dump_only=True)
	ef_id = fields.Int(dump_only=True,
                    description="If predictor was generated, id of linked extractor feature.")

class PredictorResource(MethodResource):
    @doc(tags=['predictors'], summary='Get predictor by id.')
    @marshal_with(PredictorSchema)
    def get(self, predictor_id):
        return utils.first_or_404(Predictor.query.filter_by(id=predictor_id))

class PredictorListResource(MethodResource):
	@doc(tags=['predictors'], summary='Get list of predictors.',)
	@marshal_with(PredictorSchema(many=True))
	@use_kwargs({
	    'run_id': wa.fields.DelimitedList(fields.Int(),
	                                      description="Run id(s)"),
	    'name': wa.fields.DelimitedList(fields.Str(),
	                                    description="Predictor name(s)"),
	}, locations=['query'])
	def get(self, **kwargs):
		# Get Predictors that match up to specified runs
		if 'run_id' in kwargs:
			run_id = kwargs.pop('run_id')
			kwargs['id'] = PredictorEvent.query.filter(
				PredictorEvent.run_id.in_(run_id)).distinct(
					'predictor_id').with_entities('predictor_id').all()

		query = Predictor.query
		for param in kwargs:
			query = query.filter(getattr(Predictor, param).in_(kwargs[param]))

		return query.all()

""" PredictorEvents """
class PredictorEventSchema(Schema):
    id = fields.Str(dump_only=True)
    onset = fields.Number(dump_only=True, description="Onset in seconds.")
    duration = fields.Number(dump_only=True, description="Duration in seconds.")
    value = fields.Number(dump_only=True, description="Value, or amplitude.")
    run_id = fields.Int(dump_only=True)
    predictor_id = fields.Int(dump_only=True)


class PredictorEventResource(MethodResource):
    @doc(tags=['predictors'], summary='Get predictor event by id.')
    @marshal_with(PredictorEventSchema)
    def get(self, pe_id):
        return utils.first_or_404(PredictorEvent.query.filter_by(id=pe_id))

class PredictorEventListResource(MethodResource):
    @doc(tags=['predictors'], summary='Get list of predictor events.',)
    @marshal_with(PredictorEventSchema(many=True))
    @use_kwargs({
        'run_id': wa.fields.DelimitedList(fields.Int(),
                                          description="Run id(s)",
                                          missing=[]),
        'name': wa.fields.Str(description="Predictor name",
                             load_from="predictor_name",
                             missing=''),
    }, locations=['query'])
    def get(self, **kwargs):
        query = PredictorEvent.query.filter(
            PredictorEvent.run_id.in_(kwargs['run_id'])).join(
                'predictor').filter_by(name=kwargs['name'])

        return query.all()
