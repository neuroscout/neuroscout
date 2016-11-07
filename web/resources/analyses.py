from flask_restful import Resource
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.analysis import Analysis

class AnalysisSchema(Schema):
	id = fields.Str(dump_only=True)
	# results = fields.Nested(ResultsSchema, many=True, only='id')
	name = fields.Str(required=True)
	description = fields.Str(required=True)
	# timelines = fields.Nested(TimelineSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Analysis(**data)

	class Meta:
		additional = ('dataset_id', 'user_id', 'parent')

class AnalysisResource(Resource):
	@jwt_required()
	def get(self, analysis_id):
		pass

	def put(self, analysis_id):
		pass

	def delete(self, analysis_id):
		pass

class AnalysisListResource(Resource):
	@jwt_required()
	def get(self):
		result = Analysis.query.filter_by().all()
		return AnalysisSchema(many=True).dump(result)

	def put(self):
		pass

	