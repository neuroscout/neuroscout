from flask_apispec import MethodResource, marshal_with, doc
from marshmallow import Schema, fields

from models.dataset import Dataset
from .run import RunSchema

class DatasetSchema(Schema):
	""" Dataset validation schema. """
	id = fields.Int()
	name = fields.Str(description='Dataset name')
	description = fields.Str()
	mimetypes = fields.List(fields.Str(),
                         description='Dataset mimetypes/modalities')
	tasks = fields.List(fields.Str(),
                     description='Tasks in dataset runs.')
	runs = fields.Nested(RunSchema, many=True, only='id')


class DatasetResource(MethodResource):
    @doc(tags=['dataset'], summary='Get dataset by id.')
    @marshal_with(DatasetSchema)
    def get(self, dataset_id):
    	return Dataset.query.filter_by(id=dataset_id).first_or_404()

class DatasetListResource(MethodResource):
    @doc(tags=['dataset'], summary='Returns list of datasets.')
    @marshal_with(DatasetSchema(many=True))
    def get(self):
    	return Dataset.query.all()
