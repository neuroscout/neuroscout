from flask_apispec import MethodResource, doc, marshal_with
from . import utils
from .analysis import AnalysisBundleSchema

@marshal_with(AnalysisBundleSchema(
	only=['task_name', 'design_matrix', 'preproc_address', 'config',
	      'contrasts', 'runs']))
@doc(tags=['analysis'])
class AnalysisBundleResource(MethodResource):
	@doc(summary='Get complete analysis bundled as JSON.')
	@utils.fetch_analysis
	def get(self, analysis):
		if analysis.status != "PASSED":
			utils.abort(404, "Analysis not yet compiled")
		return analysis
