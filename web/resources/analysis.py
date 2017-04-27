from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_jwt import jwt_required, current_identity
from marshmallow import Schema, fields, validates, ValidationError

from models import Analysis, Dataset
from database import db

from .predictor import PredictorSchema
from .result import ResultSchema
from .run import RunSchema

class AnalysisSchema(Schema):
	id = fields.Int(dump_only=True)
	name = fields.Str(required=True)
	description = fields.Str()

	dataset_id = fields.Int(required=True)
	user_id = fields.Int(dump_only=True)
	parent = fields.Nested('AnalysisSchema', only='id', dump_only=True)

	results = fields.Nested(
		ResultSchema, many=True, only='id', dump_only=True)
	predictors = fields.Nested(
		PredictorSchema, many=True, only='id', dump_only=True)
	runs = fields.Nested(
		RunSchema, many=True, only='id', dump_only=True)

	@validates('dataset_id')
	def validate_dsid(self, value):
		if Dataset.query.filter_by(id=value).count() == 0:
			raise ValidationError('Invalid dataset id.')

	class Meta:
		# Necessary for kwargs can also deserialize manually and catch errors
		strict = True


class AnalysisResource(MethodResource):
	""" Analysis.
    ---
    get:
		tags:
			- analysis
        summary: Get analysis by id.
        responses:
            200:
                description: successful operation
                schema: AnalysisSchema
    """
	@marshal_with(AnalysisSchema)
	def get(self, analysis_id):
		""" Access individual analysis """
		return Analysis.query.filter_by(id=analysis_id).first_or_404()

class AnalysisListResource(MethodResource):
	""" Analysis list.
    ---
    get:
		tags:
			- analysis
        summary: Returns list of analyses.
        responses:
            200:
                description: successful operation
                schema: AnalysisSchema

    """
	@marshal_with(AnalysisSchema(many=True))
	def get(self):
		""" Get a list of existing analyses """
		return Analysis.query.filter_by().all()

class AnalysisPostResource(MethodResource):
	""" Create Analysis.
	---
	post:
		tags:
			- analysis
		summary: Create a new analysis.
		responses:
			200:
				description: analysis created sucesfully.
				schema: AnalysisSchema
	"""
	@marshal_with(AnalysisSchema)
	@use_kwargs(AnalysisSchema)
	@jwt_required()
	def post(self, **kwargs):
		""" Post a new analysis """
		new = Analysis(user_id = current_identity.id, **kwargs)
		db.session.add(new)
		db.session.commit()
		return new
