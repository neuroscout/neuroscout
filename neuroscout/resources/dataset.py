from flask_apispec import MethodResource, marshal_with, doc, use_kwargs
import webargs as wa
from marshmallow import Schema, fields
from models import Dataset
from .utils import first_or_404

class DatasetSchema(Schema):
	""" Dataset validation schema. """
	id = fields.Int()
	name = fields.Str(description='Dataset name')
	description = fields.Dict()
	mimetypes = fields.List(fields.Str(),
                         description='Dataset mimetypes/modalities')
	runs = fields.Nested('RunSchema', many=True, only=['id'])
	tasks = fields.Nested('TaskSchema', many=True, only=['id', 'name'])
	dataset_address = fields.Str(description='BIDS Dataset remote address')
	preproc_address = fields.Str(description='Preprocessed data remote address')

class DatasetResource(MethodResource):
    @doc(tags=['dataset'], summary='Get dataset by id.')
    @marshal_with(DatasetSchema)
    def get(self, dataset_id):
    	return first_or_404(Dataset.query.filter_by(id=dataset_id))

class DatasetListResource(MethodResource):
	@doc(tags=['dataset'], summary='Returns list of datasets.')
	@marshal_with(DatasetSchema(many=True,
								exclude=['mimetypes', 'dataset_address', 'preproc_address']))
	@use_kwargs({
	    'active_only': wa.fields.Boolean(missing=True,
	                description="Return only active Datasets")
	    },
	    locations=['query'])
	def get(self, **kwargs):
		query = {}
		if kwargs.pop('active_only'):
			query['active'] = True
		return Dataset.query.filter_by(**query).all()
