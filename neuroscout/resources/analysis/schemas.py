from marshmallow import Schema, fields, validates, ValidationError, post_load
from models import  Dataset, Run, Predictor

class AnalysisSchema(Schema):
	""" Primary analysis schema """
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')

	config = fields.Dict(description='fMRI analysis configuration parameters.')
	contrasts = fields.List(fields.Dict(),
						    description='Array of contrasts')
	transformations = fields.List(fields.Dict(),
								  description='Array of transformation objects')

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

	description = fields.Str()
	data = fields.Dict()
	parent_id = fields.Str(dump_only=True,description="Parent analysis, if cloned.")

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

class AnalysisBundleSchema(AnalysisSchema):
	""" Bundle schema, with additional fields """
	preproc_address = fields.Nested('DatasetSchema', only='preproc_address')
	dataset_address = fields.Nested('DatasetSchema', only='dataset_address')

	design_matrix = fields.Dict(dump_only=True,
								description="Design matrix for all runs.")
	task_name = fields.Str(description='Task name', dump_only=True)
	TR = fields.Float(description='Time repetition (s)', dump_only=True)
	runs = fields.Nested(
		'RunSchema', many=True, description='Runs associated with analysis',
	    exclude=['duration', 'dataset_id', 'task'], dump_only=True)
