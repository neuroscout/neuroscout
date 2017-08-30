from flask_apispec import MethodResource, doc
from flask import current_app
from marshmallow import Schema, fields
from . import utils
from models import PredictorEvent

class AnalysisBundleSchema(Schema):
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')
	dataset_address = fields.Nested('DatasetSchema', only='address',
									load_from='dataset')
	config = fields.Dict(description='fMRI analysis configuration parameters.')

	transformations = fields.List(fields.Dict(),
							      description='Array of transformation objects')
	contrasts = fields.List(fields.Dict(),
						    description='Array of contrasts')

	task_name = fields.Str(description='Task name')

	predictor_events = fields.Nested(
		'PredictorEventSchema', many=True, description='Predictor events',
		exclude=['id'])

	runs = fields.Nested(
		'RunSchema', many=True, description='Runs associated with analysis',
	    exclude=['duration', 'dataset_id', 'task'])


@doc(tags=['analysis'])
class AnalysisBundleResource(MethodResource):
	@doc(summary='Get complete analysis bundled as JSON.')
	@utils.fetch_analysis
	def get(self, analysis):
		if analysis.status != "PASSED":
			utils.abort(404, "Analysis not yet compiled")
		pred_ids = [p.id for p in analysis.predictors]
		run_ids = [r.id for r in analysis.runs]
		analysis.predictor_events = PredictorEvent.query.filter(
		    (PredictorEvent.predictor_id.in_(pred_ids)) & \
		    (PredictorEvent.run_id.in_(run_ids))).all()

		analysis.task_name = analysis.runs[0].task.name


		return AnalysisBundleSchema().dump(analysis)
