from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from marshmallow import Schema, fields, validates, ValidationError, post_load
from database import db
from db_utils import put_record
from models import Analysis, Dataset, Run, Predictor
from . import utils

class AnalysisSchema(Schema):
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')
	dataset_id = fields.Int(required=True)
	created_at = fields.Time(dump_only=True)
	modified_at = fields.Time(dump_only=True)
	user_id = fields.Int(dump_only=True)

	status = fields.Str(
		description='Analysis status. PASSED, FAILED, PENDING, or DRAFT.',
		dump_only=True)

	compiled_at = fields.Time(description='Timestamp of when analysis was compiled',
							dump_only=True)
	private = fields.Bool(description='Analysis private or discoverable?')
	predictions = fields.Str(description='User apriori predictions.')

	config = fields.Dict(description='fMRI analysis configuration parameters.')
	description = fields.Str()
	data = fields.Dict()
	parent_id = fields.Str(dump_only=True,description="Parent analysis, if cloned.")


	transformations = fields.Nested(
		'TransformationSchema', many=True,
		description='Array of transformations'
	)
	predictors = fields.Nested(
		'PredictorSchema', many=True, only=['id'],
        description='Predictor id(s) associated with analysis')
	runs = fields.Nested(
		'RunSchema', many=True, only=['id'],
        description='Runs associated with analysis')

	results = fields.Nested(
		'ResultSchema', many=True, only=['id'], dump_only=True,
        description='Result id(s) associated with analysis')


	@validates('dataset_id')
	def validate_dsid(self, value):
		if Dataset.query.filter_by(id=value).count() == 0:
			raise ValidationError('Invalid dataset id.')

	@validates('runs')
	def validate_runs(self, value):
		try:
			[Run.query.filter_by(**r).one() for r in value]
		except:
			raise ValidationError('Invalid run id!')

	@validates('predictors')
	def validate_preds(self, value):
		try:
			[Predictor.query.filter_by(**r).one() for r in value]
		except:
			raise ValidationError('Invalid predictor id.')

	@post_load
	def nested_object(self, args):
		if 'runs' in args:
			args['runs'] = [Run.query.filter_by(**r).one() for r in args['runs']]

		if 'predictors' in args:
			args['predictors'] = [Predictor.query.filter_by(**r).one() for r in args['predictors']]

		return args

	class Meta:
		strict = True

class TransformationSchema(Schema):
	name = fields.Str(description='Transformation name.', required=True)
	inputs = fields.List(fields.Str(), required=True, description='Array of input predictors')
	parameters = fields.Nested('ParameterSchema', many=True, description='Array of parameters.')

class ParameterSchema(Schema):
	name = fields.Str(description='Parameter name.', required=True)
	kind = fields.Str(description='Parameter type (boolean or predictor).',
					  required=True)
	value = fields.Str(description='Parameter value', required=True)

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
	@utils.fetch_analysis
	def get(self, analysis):
		return analysis

	@doc(summary='Edit analysis.')
	@use_kwargs(AnalysisSchema)
	@utils.owner_required
	def put(self, analysis, **kwargs):
		if analysis.status != 'DRAFT':
			utils.abort(422, "Analysis is not editable. Try cloning it.")
		return put_record(db.session, kwargs, analysis)

	@doc(summary='Delete analysis.')
	@utils.owner_required
	def delete(self, analysis):
		if analysis.status != 'DRAFT':
			utils.abort(422, "Analysis is not editable, too bad!")
		db.session.delete(analysis)
		db.session.commit()

		return {'message' : 'deleted!'}

class CloneAnalysisResource(AnalysisBaseResource):
	@marshal_with(AnalysisSchema, code='201')
	@doc(summary='Clone analysis.')
	@utils.auth_required
	@utils.fetch_analysis
	def post(self, analysis):
		if analysis.user_id != current_identity.id:
			if analysis.status != 'PASSED':
				utils.abort(422, "You can only clone somebody else's analysis"
								  " if they have been compiled.")

		cloned = analysis.clone(current_identity)
		db.session.add(cloned)
		db.session.commit()
		return cloned

class CompileAnalysisResource(AnalysisBaseResource):
	@doc(summary='Compile and lock analysis.')
	@utils.owner_required
	def post(self, analysis):
		analysis.status = 'PENDING'

		## Add other triggers here
		db.session.add(analysis)
		db.session.commit()
		return analysis
