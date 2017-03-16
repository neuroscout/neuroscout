from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load

from models.dataset import Dataset

from .analysis import AnalysisSchema
from .run import RunSchema

from sqlalchemy.orm.exc import NoResultFound

class DatasetSchema(Schema):
	id = fields.Str(dump_only=True)

	analyses = fields.Nested(AnalysisSchema, many=True, only='id')
	runs = fields.Nested(RunSchema, many=True, only='id')

	class Meta:
		additional = ('name', 'task', 'description', 'task_description')

	@post_load
	def make_db(self, data):
		return Dataset(**data)

class DatasetResource(Resource):
	""" Individual dataset """
	@operation(
	responseMessages=[{"code": 400,
	      "message": "Dataset does not exist"}])
	@jwt_required()
	def get(self, dataset_name):
		""" Access a specific dataset """
		try:
			result = Dataset.query.filter_by(name=dataset_name).one()
			return DatasetSchema().dump(result)
		except NoResultFound:
			abort(400, message="Dataset {} does not exist".format(dataset_name))


class DatasetListResource(Resource):
	""" Available datasets """
	@operation()
	@jwt_required()
	def get(self):
		""" List of datasets """
		result = Dataset.query.filter_by().all()
		return DatasetSchema(many=True, only=['id', 'name', 'task']).dump(result)
