from flask_apispec import MethodResource, marshal_with, doc, use_kwargs
from webargs import fields
from ..models import Dataset
from ..core import cache
from .utils import first_or_404
from ..schemas.dataset import DatasetSchema


class DatasetResource(MethodResource):
    @doc(tags=['dataset'], summary='Get dataset by id.')
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    @marshal_with(DatasetSchema)
    def get(self, dataset_id):
        return first_or_404(Dataset.query.filter_by(id=dataset_id))


class DatasetListResource(MethodResource):
    @doc(tags=['dataset'], summary='Returns list of datasets.')
    @use_kwargs({
        'active_only': fields.Boolean(
            missing=True, description="Return only active Datasets"),
        'name': fields.Str(description="Dataset name"),
        },
        location='query')
    @cache.cached(60 * 60 * 24 * 300, query_string=True)
    @marshal_with(DatasetSchema(
        many=True, exclude=['dataset_address', 'preproc_address', 'runs']))
    def get(self, **kwargs):
        if kwargs.pop('active_only'):
            kwargs['active'] = True
        return Dataset.query.filter_by(**kwargs).all()
