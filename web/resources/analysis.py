from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from marshmallow import Schema, fields, validates, ValidationError
from database import db
from db_utils import put_record
from models import Analysis, Dataset
from . import utils
import datetime

class AnalysisSchema(Schema):
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')
	dataset_id = fields.Int(required=True)
	created_at = fields.Time(dump_only=True)
	modified_at = fields.Time(dump_only=True)
	user_id = fields.Int(dump_only=True)

	locked = fields.Bool(
		description='Is analysis finished and locked? Locking is irreversible.')
	locked_at = fields.Time(description='Timestamp of when analysis was locked',
							dump_only=True)
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


	@validates('dataset_id')
	def validate_dsid(self, value):
		if Dataset.query.filter_by(id=value).count() == 0:
			raise ValidationError('Invalid dataset id.')

	class Meta:
		strict = True

@doc(tags=['analysis'])
@marshal_with(AnalysisSchema)
class AnalysisBaseResource(MethodResource):
	pass

class AnalysisRootResource(AnalysisBaseResource):
	"""" Resource for root address """
	@marshal_with(AnalysisSchema(many=True))
	@doc(summary='Returns list of public analyses.')
	def get(self):
		return Analysis.query.filter_by(private=False).all()

	@marshal_with(AnalysisSchema, code='201')
	@doc(summary='Add new analysis.')
	@use_kwargs(AnalysisSchema)
	@utils.auth_required
	def post(self, **kwargs):
		new = Analysis(user_id = current_identity.id, **kwargs)
		db.session.add(new)
		db.session.commit()
		return new

class AnalysisResource(AnalysisBaseResource):
	@doc(summary='Get analysis by id.')
	def get(self, analysis_id):
		return utils.first_or_404(Analysis.query.filter_by(hash_id=analysis_id))

	@doc(summary='Edit analysis.')
	@use_kwargs(AnalysisSchema)
	@utils.auth_required
	def put(self, analysis_id, **kwargs):
		analysis = utils.first_or_404(
			Analysis.query.filter_by(hash_id=analysis_id))
		if analysis.locked is True:
			utils.abort(422, "Analysis is not editable. Try cloning it.")
		else:
			if kwargs['locked'] > analysis.locked:
				kwargs['locked_at'] = datetime.datetime.utcnow()
				### Add other triggers here
			return put_record(db.session, kwargs, analysis)

class CloneAnalysisResource(AnalysisBaseResource):
	@marshal_with(AnalysisSchema, code='201')
	@doc(summary='Clone analysis.')
	@utils.auth_required
	def post(self, analysis_id):
		original = utils.first_or_404(
			Analysis.query.filter_by(hash_id=analysis_id))
		if original.locked is False:
			utils.abort(422, "Only locked analyses can be cloned")
		else:
			cloned = original.clone()
			db.session.add(cloned)
			db.session.commit()
			return cloned
