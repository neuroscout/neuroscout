from flask import request
from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required, current_identity
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.analysis import Analysis
from models.dataset import Dataset

from database import db

from .predictor import PredictorSchema
from .result import ResultSchema
from .run import RunSchema

class AnalysisSchema(Schema):
	id = fields.Int(dump_only=True)
	name = fields.Str(required=True)
	description = fields.Str(required=True)

	dataset_id = fields.Str(required=True)
	user_id = fields.Int(required=True, dump_only=True)
	parent = fields.Nested('AnalysisSchema', only='id')

	results = fields.Nested(ResultSchema, many=True, only='id')
	predictors = fields.Nested(PredictorSchema, many=True, only='id')
	runs = fields.Nested(RunSchema, many=True, only='id')


	@post_load
	def make_db(self, data):
		return Analysis(**data)

	@validates('dataset_id')
	def validate_dsid(self, value):
		if Dataset.query.filter_by(id=value).count() == 0:
			raise ValidationError('Invalid dataset id.')

	class Meta:
		additional = ('user_id', )

class AnalysisResource(Resource):
	""" User generated analysis """
	@operation()
	def get(self, analysis_id):
		""" Access individual analysis """
		result = Analysis.query.filter_by(id=analysis_id).first_or_404()
		return AnalysisSchema().dump(result)

class AnalysisListResource(Resource):
	""" User generated analyses """
	@operation()
	def get(self):
		""" Get a list of existing analyses """
		result = Analysis.query.filter_by().all()
		return AnalysisSchema(many=True).dump(result)

	@operation(
	responseMessages=[{"code": 405,
	      "message": "Invalid input"}])
	@jwt_required()
	def post(self):
		""" Post a new analysis """
		data = request.get_json()
		new, errors = AnalysisSchema().load(data)

		if errors:
			abort(405 , errors=errors)
		else:
			new.user_id = current_identity.id
			db.session.add(new)
			db.session.commit()
			return AnalysisSchema().dump(new)

	## Return some information like the analysis id
