from flask_restful import Resource
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load

from models.dataset import Dataset

from .run import RunSchema


class DatasetSchema(Schema):
	runs = fields.Nested(RunSchema, many=True, only='id')

	class Meta:
		additional = ('id', 'description', 'mimetypes', 'tasks')

	@post_load
	def make_db(self, data):
		return Dataset(**data)

class DatasetResource(Resource):
	""" Individual dataset """
	@operation(
	responseMessages=[{"code": 404,
	      "message": "Dataset does not exist"}])
	@jwt_required()
	def get(self, dataset_id):
		""" Access a specific dataset """
		result = Dataset.query.filter_by(id=dataset_id).first_or_404()
		return DatasetSchema().dump(result)

class DatasetListResource(Resource):
	""" Available datasets """
	@operation()
	@jwt_required()
	def get(self):
		""" List of datasets """
		result = Dataset.query.all()
		return DatasetSchema(many=True, only=['id', 'mimetypes', 'tasks']).dump(result)
