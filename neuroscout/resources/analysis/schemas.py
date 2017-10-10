from marshmallow import Schema, fields, validates, ValidationError, post_load
from models import  Dataset, Run, Predictor

class AnalysisSchema(Schema):
	""" Primary analysis schema """
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	parent_id = fields.Str(dump_only=True,description="Parent analysis, if cloned.")
	user_id = fields.Int(dump_only=True)

	name = fields.Str(required=True, description='Analysis name.')
	description = fields.Str()
	predictions = fields.Str(description='User apriori predictions.')

	dataset_id = fields.Int(required=True)
	task_name = fields.Str(description='Task name', dump_only=True)
	TR = fields.Float(description='Time repetition (s)', dump_only=True)

	config = fields.Dict(description='fMRI analysis configuration parameters.')
	contrasts = fields.List(fields.Dict(),
						    description='Array of contrasts')
	transformations = fields.List(fields.Dict(),
								  description='Array of transformation objects')

	created_at = fields.Time(dump_only=True)
	modified_at = fields.Time(dump_only=True)
	compiled_at = fields.Time(description='Timestamp of when analysis was compiled',
							dump_only=True)
	status = fields.Str(description='PASSED, FAILED, PENDING, or DRAFT.',
		dump_only=True)

	private = fields.Bool(description='Analysis private or discoverable?')

	data = fields.Dict()

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

class AnalysisFullSchema(AnalysisSchema):
	""" Analysis schema, with additional nested fields """
	runs = fields.Nested(
		'RunSchema', many=True, description='Runs associated with analysis',
	    exclude=['duration', 'dataset_id', 'task'], dump_only=True)

	predictors = fields.Nested(
		'PredictorSchema', many=True, only=['id', 'name'],
        description='Predictor id(s) associated with analysis', dump_only=True)

class AnalysisResourcesSchema(Schema):
	""" Schema for Analysis resources. """
	preproc_address = fields.Nested(
		'DatasetSchema', only='preproc_address', attribute='dataset')
	dataset_address = fields.Nested(
		'DatasetSchema', only='dataset_address', attribute='dataset')
	func_paths = fields.Nested(
		'RunSchema', many=True, only='func_path', attribute='runs')
	mask_paths = fields.Nested(
		'RunSchema', many=True, only='mask_path', attribute='runs')

class DesignEventsSchema(Schema):
	# Nested dataset fields
	trial_type = fields.Str(description='Predictor id.', attribute='condition')
	amplitude = fields.Float()
	duration = fields.Float()
	onset = fields.Float()
	session = fields.Str(description='Session number')
	subject = fields.Str(description='Subject id')
	number = fields.Str(description='Run id', attribute='run')
