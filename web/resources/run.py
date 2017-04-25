from flask_restful import Resource
from flask_restful_swagger.swagger import operation
from marshmallow import Schema, fields
from models import Run, Dataset

from flask import request
import webargs as wa
from webargs.flaskparser import parser


class RunSchema(Schema):
	id = fields.Str(dump_only=True)
	class Meta:
		additional = ('session', 'subject', 'number', 'task', 'duration',
					  'task_description', 'TR', 'path', 'dataset_id')

class RunResource(Resource):
	""" Resource for Run """
	@operation()
	def get(self, run_id):
		""" Access a run """
		result = Run.query.filter_by(id=run_id).first_or_404()
		return RunSchema().dump(result)

class RunListResource(Resource):
	""" Available runs """
	@operation()
	def get(self):
		""" List of runs """
		user_args = {
		    'session': wa.fields.DelimitedList(fields.Str()),
		    'number': wa.fields.DelimitedList(fields.Str()),
		    'task': wa.fields.DelimitedList(fields.Str()),
		    'subject': wa.fields.DelimitedList(fields.Str()),
		    'dataset_id': wa.fields.Str(),
			'all_fields': wa.fields.Bool(missing=False)
		}
		args = parser.parse(user_args, request)

		marsh_args = {'many' : True}
		if not args.pop('all_fields'):
			marsh_args['only'] = \
			['id', 'dataset_id', 'session', 'subject', 'number', 'task']

		try:
			dataset = args.pop('dataset_id')
		except KeyError:
			dataset = None

		query = Run.query
		for param in args:
			query = query.filter(getattr(Run, param).in_(args[param]))

		if dataset:
			query = query.join('dataset').filter_by(id=dataset)

		return RunSchema(**marsh_args).dump(query.all())
