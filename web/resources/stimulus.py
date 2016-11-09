from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.stimulus import Stimulus

from .predictor import PredictorSchema

class StimulusSchema(Schema):
	id = fields.Str(dump_only=True)
	predictors = fields.Nested(PredictorSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Stimulus(**data)

	class Meta:
		additional = ('dataset_id', )

class StimulusResource(Resource):
	@operation()
	@jwt_required()
	def get(self, stimulus_id):
		result = Stimulus.query.filter_by(id=stimulus_id).one()
		if result:
			return StimulusSchema().dump(result)
		else:
			abort(400, message="Stimulus {} doesn't exist".format(stimulus_id))
