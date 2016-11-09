from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.predictor import Predictor
from .event import EventSchema

class PredictorSchema(Schema):
	id = fields.Str(dump_only=True)
	stimuli = fields.Nested(EventSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Predictor(**data)

	class Meta:
		additional = ('stimulus_id', 'extractor_id')

class PredictorResource(Resource):
	""" Extracted predictors """
	@operation(
	responseMessages=[
	    {
	      "code": 400,
	      "message": "Predictor doesn't exist"
	    },
	  ]
	)
	@jwt_required()
	def get(self, timeline_id):
		""" Access extracted predictor """
		result = Predictor.query.filter_by(id=timeline_id).one()
		if result:
			return PredictorSchema().dump(result)
		else:
			abort(400, message="Predictor {} doesn't exist".format(timeline_id))

class PredictorListResource(Resource):
	""" Extracted predictors """
	@operation()
	@jwt_required()
	def get(self):
		""" List of extracted predictors """
		result = Predictor.query.filter_by().all()
		return PredictorSchema(many=True).dump(result)