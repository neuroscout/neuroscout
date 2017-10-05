from flask import current_app
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from worker import celery_app
from marshmallow import Schema, fields, validates, ValidationError, post_load
from database import db
from db_utils import put_record
from models import Analysis, Dataset, Run, Predictor, PredictorEvent
from . import utils
from .predictor import PredictorEventSchema

class AnalysisSchema(Schema):
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')
	preproc_address = fields.Nested('DatasetSchema', only='preproc_address')

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
	design_matrix = fields.Dict(dump_only=True,
								description="Design matrix for all runs.")
	task_name = fields.Str(description='Task name', dump_only=True)
	runs = fields.Nested(
		'RunSchema', many=True, description='Runs associated with analysis',
	    exclude=['duration', 'dataset_id', 'task'], dump_only=True)

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

	@marshal_with(AnalysisSchema)
	@use_kwargs(AnalysisSchema)
	@doc(summary='Add new analysis!')
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
			exceptions = ['private']
			kwargs = {k: v for k, v in kwargs.items() if k in exceptions}
			if not kwargs:
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
	@marshal_with(AnalysisSchema)
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

def get_predictor_events(analysis):
	pred_ids = [p.id for p in analysis.predictors]
	run_ids = [r.id for r in analysis.runs]
	return PredictorEvent.query.filter(
	    (PredictorEvent.predictor_id.in_(pred_ids)) & \
	    (PredictorEvent.run_id.in_(run_ids))).all()

class CompileAnalysisResource(AnalysisBaseResource):
	@marshal_with(AnalysisSchema)
	@doc(summary='Compile and lock analysis.')
	@utils.owner_required
	def post(self, analysis):
		analysis.status = 'PENDING'
		analysis_json = AnalysisBundleSchema().dump(analysis)[0]
		pes_json = PredictorEventSchema(many=True, exclude=['id']).dump(
			get_predictor_events(analysis))[0]

		task = celery_app.send_task('workflow.compile',
				args=[analysis_json, pes_json,
				analysis.dataset.local_path])
		analysis.celery_id = task.id

		db.session.add(analysis)
		db.session.commit()
		current_app.logger
		return analysis

@doc(tags=['analysis'])
class AnalysisGraphResource(MethodResource):
	@doc(summary='Get analysis nipype workflow graph.',
		 produces=["image/png"],
		 responses={"default": {
			 "description" : "Nipype workflow python executable." }})
	@utils.auth_required
	@utils.fetch_analysis
	def get(self, analysis):
		if analysis.status != "PASSED":
			utils.abort(404, "Analysis not yet compiled")
		return analysis.workflow
