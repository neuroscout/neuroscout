from flask_apispec import MethodResource, marshal_with
from marshmallow import Schema, fields

from models.dataset import Dataset
from .run import RunSchema

class DatasetSchema(Schema):
	""" Dataset validation schema. """
	id = fields.Int()
	name = fields.Str()
	description = fields.Str()
	mimetypes = fields.List(fields.Str())
	tasks = fields.List(fields.Str())
	runs = fields.Nested(RunSchema, many=True, only='id')


class DatasetResource(MethodResource):
	""" Dataset
    ---
    get:
        summary: Get dataset by id.
        responses:
            200:
                description: successful operation
                schema: DatasetSchema
    """
	@marshal_with(DatasetSchema)
	def get(self, dataset_id):
		return Dataset.query.filter_by(id=dataset_id).first_or_404()

class DatasetListResource(MethodResource):
	""" Dataset list.
    ---
    get:
        summary: Returns list of datasets.
        responses:
            200:
                description: successful operation
                schema: DatasetSchema
    """
	@marshal_with(DatasetSchema(many=True))
	def get(self):
		return Dataset.query.all()
