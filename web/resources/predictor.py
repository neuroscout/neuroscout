from marshmallow import Schema, fields
from models import Predictor, PredictorEvent, Run

from flask import request
import webargs as wa
from webargs.flaskparser import parser

# Predictor Event Resources
class PredictorEventSchema(Schema):
	id = fields.Str(dump_only=True)

	class Meta:
		additional = ('onset', 'duration', 'value', 'run_id', 'predictor_id')

# Predictor Resources
class PredictorSchema(Schema):
	id = fields.Str(dump_only=True)

	predictor_events = fields.Nested(PredictorEventSchema, many=True, only='id')

	class Meta:
		additional = ('name', 'description', 'ef_id', 'analysis')
#
# class PredictorResource(Resource):
# 	""" Predictors """
# 	@operation()
# 	def get(self, predictor_id):
# 		""" Access a predictor by id """
# 		result = Predictor.query.filter_by(id=predictor_id).first_or_404()
# 		return PredictorSchema().dump(result)
#
# class PredictorListResource(Resource):
# 	""" Extracted predictors """
# 	@operation()
# 	def get(self):
# 		""" List of extracted predictors """
# 		user_args = {
# 			'all_fields': wa.fields.Bool(missing=False),
# 		    'run_id': wa.fields.DelimitedList(fields.Str()),
# 		    'name': wa.fields.DelimitedList(fields.Str()),
# 		}
# 		args = parser.parse(user_args, request)
# 		marsh_args = {'many' : True}
# 		if not args.pop('all_fields'):
# 			marsh_args['only'] = \
# 			['id', 'name']
#
# 		try:
# 			run_ids = args.pop('run_id')
# 		except KeyError:
# 			run_ids = None
#
# 		query = Predictor.query
# 		for param in args:
# 			query = query.filter(getattr(Predictor, param).in_(args[param]))
#
# 		if run_ids:
# 			query = query.join('predictor_events').filter(
# 				PredictorEvent.run_id.in_(run_ids))
#
# 		return PredictorSchema(**marsh_args).dump(query.all())
