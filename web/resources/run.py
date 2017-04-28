from marshmallow import Schema, fields
from models import Run
from flask_apispec import MethodResource, marshal_with, use_kwargs
import webargs as wa

class RunSchema(Schema):
	id = fields.Int()
	session = fields.Str()
	subject = fields.Str()
	number = fields.Str()
	task = fields.Str()
	duration = fields.Number()
	task_description = fields.Str()
	TR = fields.Number()
	path = fields.Str()
	dataset_id = fields.Int()

class RunResource(MethodResource):
    @marshal_with(RunSchema(many=True))
    def get(self, run_id):
        """ Run.
        ---
    	get:
    		summary: Get run by id.
    		responses:
    			200:
    				description: successful operation
    				schema: RunSchema
        """
        return Run.query.filter_by(id=run_id).first_or_404()

class RunListResource(MethodResource):
    @marshal_with(RunSchema(many=True))
    @use_kwargs({
    	'session': wa.fields.DelimitedList(fields.Str()),
        'number': wa.fields.DelimitedList(fields.Str()),
        'task': wa.fields.DelimitedList(fields.Str()),
        'subject': wa.fields.DelimitedList(fields.Str()),
        'dataset_id': wa.fields.Int(),
    })
    def get(self, **kwargs):
        """ Run list.
        ---
        get:
            description: Returns list of runs.
            responses:
                200:
                    description: successful operation
                    schema: RunSchema
        """
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
