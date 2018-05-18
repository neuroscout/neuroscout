from marshmallow import Schema, fields
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
import webargs as wa
from ..models import Run
from .utils import first_or_404

class RunSchema(Schema):
	id = fields.Int()
	session = fields.Str(description='Session number')
	subject = fields.Str(description='Subject id')
	number = fields.Str(description='Run id')
	duration = fields.Number(description='Total run duration in seconds.')
	dataset_id = fields.Int(description='Dataset run belongs to.')
	task = fields.Nested('TaskSchema', only=['id', 'name'],
	                    description="Task id and name")
	func_path = fields.Str(description='Path of functional file')
	mask_path = fields.Str(description='Path of brain mask')

exclude = ['func_path', 'mask_path']
class RunResource(MethodResource):
    @doc(tags=['run'], summary='Get run by id.')
    @marshal_with(RunSchema(exclude=exclude))
    def get(self, run_id):
        return first_or_404(Run.query.filter_by(id=run_id))

class RunListResource(MethodResource):
    @doc(tags=['run'], summary='Returns list of runs.')
    @use_kwargs({
    	'session': wa.fields.DelimitedList(fields.Str(),
                                        description='Session number(s).'),
        'number': wa.fields.DelimitedList(fields.Str(),
                                          description='Run number(s).'),
        'task_id': wa.fields.DelimitedList(fields.Int(),
                                        description='Task id(s).'),
        'subject': wa.fields.DelimitedList(fields.Str(),
                                           description='Subject id(s).'),
        'dataset_id': wa.fields.Int(description='Dataset id.'),
    }, locations=['query'])
    @marshal_with(RunSchema(many=True, exclude=exclude))
    def get(self, **kwargs):
        try:
            dataset = kwargs.pop('dataset_id')
        except KeyError:
        	dataset = None

        query = Run.query
        for param in kwargs:
        	query = query.filter(getattr(Run, param).in_(kwargs[param]))

        if dataset:
        	query = query.join('dataset').filter_by(id=dataset)
        return query.all()
