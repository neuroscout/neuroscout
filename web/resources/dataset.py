from flask_apispec import MethodResource, marshal_with
from marshmallow import Schema, fields

from models.dataset import Dataset
from .run import RunSchema

from flask_jwt import jwt_required

class DatasetSchema(Schema):
	runs = fields.Nested(RunSchema, many=True, only='id')

	class Meta:
		additional = ('id', 'name', 'description', 'mimetypes', 'tasks')

@marshal_with(DatasetSchema)
class DatasetResource(MethodResource):
	def get(self, dataset_id):
		""" Retrieve a dataset resource.  """
		return Dataset.query.filter_by(id=dataset_id).first_or_404()

@marshal_with(DatasetSchema(many=True))
class DatasetListResource(MethodResource):
	def get(self):
		""" List of datasets """
		return Dataset.query.all()
