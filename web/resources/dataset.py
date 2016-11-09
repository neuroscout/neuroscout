from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError

from models.dataset import Dataset

from .analysis import AnalysisSchema
from .stimulus import StimulusSchema

class DatasetSchema(Schema):
	id = fields.Str(dump_only = True)
	external_id = fields.Str(required=True)
	analyses = fields.Nested(AnalysisSchema, many=True, only='id')
	stimuli = fields.Nested(StimulusSchema, many=True, only='id')
	name = fields.Str(required=True)

	@validates('name')
	def validate_name(self, value):
		if len(value) < 5:
			raise ValidationError('Name must be longer than 5 characters.')

	@post_load
	def make_db(self, data):
		return Dataset(**data)

	class Meta:
		additional = ("events", "attributes")

class DatasetResource(Resource):
	@operation()
	@jwt_required()
	def get(self, dataset_id):
		result = Dataset.query.filter_by(external_id=dataset_id).one()
		if result:
			return DatasetSchema().dump(result)
		else:
			abort(400, message="Dataset {} doesn't exist".format(dataset_id))


class DatasetListResource(Resource):
	@operation()
	@jwt_required()
	def get(self):
		result = Dataset.query.filter_by().all()
		return DatasetSchema(many=True).dump(result)
