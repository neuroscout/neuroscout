from flask_restful import Resource
from flask_restful_swagger.swagger import operation
from marshmallow import Schema, fields, post_load

from models.dataset import Dataset

from .run import RunSchema

from flask import request
import webargs as wa
from webargs.flaskparser import parser

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
	def get(self, dataset_id):
		""" Access a specific dataset """
		result = Dataset.query.filter_by(id=dataset_id).first_or_404()
		return DatasetSchema().dump(result)

class DatasetListResource(Resource):
	""" Available datasets """
	@operation()
	def get(self):
		""" List of datasets """
		user_args = {
			'all_fields': wa.fields.Bool(missing=False)
		}
		args = parser.parse(user_args, request)

		marsh_args = {'many' : True}
		if not args.pop('all_fields'):
			marsh_args['only'] = \
			['id', 'mimetypes', 'tasks']
		result = Dataset.query.all()
		return DatasetSchema(**marsh_args).dump(result)
