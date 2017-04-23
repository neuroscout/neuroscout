from flask_restful import Resource
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from flask import request
from marshmallow import Schema, fields
from models.run import Run

class RunSchema(Schema):
	id = fields.Str(dump_only=True)
	class Meta:
		additional = ('session', 'subject', 'number', 'task', 'duration',
					  'task_description', 'TR', 'path', 'dataset_id')

class RunResource(Resource):
	""" Resource for Run """
	@operation()
	@jwt_required()
	def get(self, run_id):
		""" Access a run """
		result = Run.query.filter_by(id=run_id).first_or_404()
		return RunSchema().dump(result)

class RunListResource(Resource):
	""" Available datasets """
	@operation()
	@jwt_required()
	def get(self):
		""" List of datasets """
		filters_run = {}
		filters_dataset = {}
		for arg in request.args:
			if arg in ['session', 'subject', 'number', 'task']:
				filters_run[arg] = request.args[arg]
			elif arg in ['dataset']:
				filters_dataset['name'] = request.args['dataset']

		result = Run.query.filter_by(**filters_run).join(
			'dataset').filter_by(**filters_dataset).all()
		return RunSchema(many=True,
			only=['session', 'subject', 'number', 'task']).dump(result)
