from flask import send_file
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from worker import celery_app
from database import db
from db_utils import put_record
from models import Analysis, PredictorEvent
from os.path import exists

from .. import utils
from ..predictor import PredictorEventSchema
from .schemas import (AnalysisSchema, AnalysisFullSchema,
					 AnalysisResourcesSchema)

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
		if analysis.status not in ['DRAFT', 'FAILED']:
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


def json_analysis(analysis):
	analysis_json = AnalysisFullSchema().dump(analysis)[0]

	pred_ids = [p.id for p in analysis.predictors]
	run_ids = [r.id for r in analysis.runs]
	pes = PredictorEvent.query.filter(
	    (PredictorEvent.predictor_id.in_(pred_ids)) & \
	    (PredictorEvent.run_id.in_(run_ids))).all()
	pes_json = PredictorEventSchema(many=True, exclude=['id']).dump(pes)[0]

	resources_json = AnalysisResourcesSchema().dump(analysis)[0]

	return analysis_json, pes_json, resources_json

class CompileAnalysisResource(AnalysisBaseResource):
	@doc(summary='Compile and lock analysis.')
	@utils.owner_required
	def post(self, analysis):
		analysis.status = 'PENDING'
		task = celery_app.send_task('workflow.compile',
				args=[*json_analysis(analysis),
				analysis.dataset.local_path])
		analysis.celery_id = task.id

		db.session.add(analysis)
		db.session.commit()
		return analysis

class AnalysisFullResource(AnalysisBaseResource):
	@marshal_with(AnalysisFullSchema)
	@doc(summary='Get analysis (including nested fields).')
	@utils.fetch_analysis
	def get(self, analysis):
		return analysis

class AnalysisResourcesResource(AnalysisBaseResource):
	@marshal_with(AnalysisResourcesSchema)
	@doc(summary='Get analysis resources.')
	@utils.fetch_analysis
	def get(self, analysis):
		return analysis

class AnalysisBundleResource(MethodResource):
	@doc(tags=['analysis'], summary='Get analysis tarball bundle.',
	responses={"200": {
		"description": "gzip tarball, including analysis, resources and events.",
		"type": "application/x-tar"}})
	@utils.fetch_analysis
	def get(self, analysis):
		if (analysis.status != "PASSED" or analysis.bundle_path is None or \
		not exists(analysis.bundle_path)):
			msg = "Analysis bundle not available. Try compiling."
			utils.abort(404, msg)
		return send_file(analysis.bundle_path, as_attachment=True)
