from flask_apispec import MethodResource, doc
from marshmallow import Schema, fields
from . import utils
from models import PredictorEvent

class AnalysisBundleSchema(Schema):
	hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
	name = fields.Str(required=True, description='Analysis name.')
	dataset = fields.Nested('DatasetSchema', only='address')
	config = fields.Dict(description='fMRI analysis configuration parameters.')

	transformations = fields.List(fields.Dict(),
							      description='Array of transformation objects')
	contrasts = fields.List(fields.Dict(),
						    description='Array of contrasts')

	task_name = fields.Str(description='Task name')
	predictors = fields.Nested('PredictorSchema', many=True, only=['id', 'name'])

	predictor_events = fields.Nested(
		'PredictorEventSchema', many=True, description='Predictor events',
		exclude=['id', 'predictor_id'])
	runs = fields.Nested(
		'RunSchema', many=True, description='Runs associated with analysis',
	    only=['id', 'subject', 'session', 'number'])


@doc(tags=['analysis'])
class AnalysisBundleResource(MethodResource):
	@doc(summary='Get complete analysis bundled as JSON.')
	@utils.fetch_analysis
	def get(self, analysis):
		if analysis.status != "PASSED":
			utils.abort(404, "Analysis not yet compiled")
		pred_ids = [p.id for p in analysis.predictors]
		run_ids = [r.id for r in analysis.runs]
		analysis.task_name = analysis.runs[0].task.name

		analysis.predictor_events = PredictorEvent.query.filter(
		    (PredictorEvent.predictor_id.in_(pred_ids)) & \
		    (PredictorEvent.run_id.in_(run_ids))).all()

		return AnalysisBundleSchema().dump(analysis)
