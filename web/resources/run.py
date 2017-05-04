from marshmallow import Schema, fields
from models import Run
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
import webargs as wa

class RunSchema(Schema):
	id = fields.Int()
	session = fields.Str(description='Session number')
	subject = fields.Str(description='Subject id')
	number = fields.Str(description='Run id')
	task = fields.Str(description='Task name')
	duration = fields.Number(description='Total run duration in seconds.')
	task_description = fields.Dict(description='BIDS description of task (JSON).')
	TR = fields.Number(description='Aquisition repetition time.')
	dataset_id = fields.Int(description='Dataset run belongs to.')

class RunResource(MethodResource):
    @doc(tags=['run'], summary='Get run by id.')
    @marshal_with(RunSchema)
    def get(self, run_id):
        return Run.query.filter_by(id=run_id).first_or_404()

class RunListResource(MethodResource):
    @doc(tags=['run'], summary='Returns list of runs.')
    @use_kwargs({
    	'session': wa.fields.DelimitedList(fields.Str(),
                                        description='Session number(s).'),
        'number': wa.fields.DelimitedList(fields.Str(),
                                          description='Run number(s).'),
        'task': wa.fields.DelimitedList(fields.Str(),
                                        description='Task name(s).'),
        'subject': wa.fields.DelimitedList(fields.Str(),
                                           description='Subject id(s).'),
        'dataset_id': wa.fields.Int(description='Dataset id.'),
    }, locations=['query'])
    @marshal_with(RunSchema(many=True))
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
