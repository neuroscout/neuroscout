from flask_apispec import MethodResource, marshal_with, use_kwargs, doc, Ref
from flask_jwt import current_identity
from marshmallow import Schema, fields, validates, ValidationError
from database import db
from models import Analysis, Dataset
from .utils import auth_required, abort

class AnalysisSchema(Schema):
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')
	dataset_id = fields.Int(required=True)

	locked = fields.Bool(description='Analysis editable?', dump_only=True)
	private = fields.Bool(description='Analysis private or discoverable?')

	transformations = fields.Dict(description='Transformation json spec.')
	description = fields.Str()
	data = fields.Dict()
	parent_id = fields.Str(dump_only=True,
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

@doc(tags=['analysis'])
@marshal_with(Ref('schema'))
class AnalysisBaseResource(MethodResource):
	schema = AnalysisSchema

class AnalysisListResource(AnalysisBaseResource):
	schema = AnalysisSchema(many=True)
	@doc(summary='Returns list of analyses.')
	def get(self):
		return Analysis.query.all()


class AnalysisResource(AnalysisBaseResource):
    @doc(summary='Get analysis by id.')
    def get(self, analysis_id):
    	return Analysis.query.filter_by(hash_id=analysis_id).first_or_404()


class CreateAnalysisResource(AnalysisBaseResource):
	@doc(summary='Add new analysis.')
	@use_kwargs(AnalysisSchema)
	@auth_required
	def post(self, **kwargs):
		new = Analysis(user_id = current_identity.id, **kwargs)
		db.session.add(new)
		db.session.commit()
		return new

class CloneAnalysisResource(AnalysisBaseResource):
	@doc(summary='Clone analysis.')
	@auth_required
	def post(self, analysis_id):
		original = Analysis.query.filter_by(hash_id=analysis_id).first_or_404()
		# if original.locked is False:
		# 	abort(422, "Only locked analyses can be cloned")
		# else:
		cloned = original.clone()
		db.session.add(cloned)
		db.session.commit()
		print(cloned.hash_id)
		return cloned
		### YOU CAN ONLY CLONE COMPLTE add_analyses

#PUT
## End point for "submitting analysis"
