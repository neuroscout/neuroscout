from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import jwt_required, current_identity
from marshmallow import Schema, fields, validates, ValidationError
from database import db
from models import Analysis, Dataset
from hashids import Hashids
from flask import current_app

class AnalysisSchema(Schema):
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')
	dataset_id = fields.Int(required=True)

	status = fields.Str(description='Analysis completeness status.')
	transformations = fields.Dict(description='Transformation json spec.')
	description = fields.Str()
	data = fields.Dict()
	parent = fields.Nested('AnalysisSchema', only='id', dump_only=True,
                        description="Parent analysis, if cloned.")


	predictors = fields.Nested(
		'PredictorSchema', many=True, only='id',
        description='Predictor id(s) associated with analysis')
	runs = fields.Nested(
		'RunSchema', many=True, only='id',
        description='Runs associated with analysis')

	results = fields.Nested(
		'ResultSchema', many=True, only='id', dump_only=True,
        description='Result id(s) associated with analysis')
	user_id = fields.Int(dump_only=True)


	@validates('dataset_id')
	def validate_dsid(self, value):
		if Dataset.query.filter_by(id=value).count() == 0:
			raise ValidationError('Invalid dataset id.')

	class Meta:
		strict = True


class AnalysisResource(MethodResource):
    @doc(tags=['analysis'], summary='Get analysis by hash id.')
    @marshal_with(AnalysisSchema)
    def get(self, analysis_id):
    	return Analysis.query.filter_by(hash_id=analysis_id).first_or_404()

class AnalysisListResource(MethodResource):
    @doc(tags=['analysis'], summary='Returns list of analyses.')
    @marshal_with(AnalysisSchema(many=True))
    def get(self):
    	return Analysis.query.all()

class AnalysisPostResource(MethodResource):
	@doc(params={"authorization": {
	    "in": "header", "required": True,
	    "description": "Format:  JWT {authorization_token}"}})
	@jwt_required()
	@doc(tags=['analysis'], summary='Add a new analysis.')
	@marshal_with(AnalysisSchema)
	@use_kwargs(AnalysisSchema)
	def post(self, **kwargs):
		new = Analysis(user_id = current_identity.id, **kwargs)
		db.session.add(new)
		db.session.flush()
		new.hash_id = Hashids(current_app.config['HASH_SALT']).encode(new.id)
		db.session.commit()
		return new
