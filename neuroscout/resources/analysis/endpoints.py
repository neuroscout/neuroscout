from flask import send_file
from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from flask_jwt import current_identity
from worker import celery_app
from database import db
from sqlalchemy.dialects import postgresql
from models import Analysis, PredictorEvent
from os.path import exists

from utils.db import put_record
from ..utils import owner_required, auth_required, fetch_analysis, abort
from .schemas import (AnalysisSchema, AnalysisFullSchema,
					 AnalysisResourcesSchema, AnalysisCompiledSchema)

@doc(tags=['analysis'])
@marshal_with(AnalysisSchema)
class AnalysisBaseResource(MethodResource):
	pass

class AnalysisRootResource(AnalysisBaseResource):
	"""" Resource for root address """
	@marshal_with(AnalysisSchema(many=True))
	@doc(summary='Returns list of public analyses.')
	def get(self):
		return Analysis.query.filter_by(private=False, status='PASSED').all()

	@use_kwargs(AnalysisSchema)
	@doc(summary='Add new analysis!')
	@auth_required
	def post(self, **kwargs):
		new = Analysis(user_id = current_identity.id, **kwargs)
		db.session.add(new)
		db.session.commit()
		return new

class AnalysisResource(AnalysisBaseResource):
	@doc(summary='Get analysis by id.')
	@fetch_analysis
	def get(self, analysis):
		return analysis

	@doc(summary='Edit analysis.')
	@use_kwargs(AnalysisSchema)
	@owner_required
	def put(self, analysis, **kwargs):
		if analysis.status not in ['DRAFT', 'FAILED']:
			exceptions = ['private', 'description']
			kwargs = {k: v for k, v in kwargs.items() if k in exceptions}
			if not kwargs:
				abort(422, "Analysis is not editable. Try cloning it.")
		return put_record(kwargs, analysis)

	@doc(summary='Delete analysis.')
	@owner_required
	def delete(self, analysis):
		if analysis.status != 'DRAFT':
			abort(422, "Analysis is not editable, too bad!")
		db.session.delete(analysis)
		db.session.commit()

		return {'message' : 'deleted!'}

class CloneAnalysisResource(AnalysisBaseResource):
	@doc(summary='Clone analysis.')
	@auth_required
	@fetch_analysis
	def post(self, analysis):
		if analysis.user_id != current_identity.id:
			if analysis.status != 'PASSED':
				abort(422, "You can only clone somebody else's analysis"
								  " if they have been compiled.")

		cloned = analysis.clone(current_identity)
		db.session.add(cloned)
		db.session.commit()
		return cloned

def dump_pe(pes):
	""" Custom function to serialize PredictorEvent, build for *SPEED*
	Uses Core SQL queries. Warning: relies on attributes being in correct
	order. """
	statement = str(pes.statement.compile(dialect=postgresql.dialect()))
	params = pes.statement.compile(dialect=postgresql.dialect()).params
	res = db.session.connection().execute(statement, params)
	return [{
	  'onset': r[1],
	  'duration': r[2],
	  'value':  r[3],
	  'run_id': r[5],
	  'predictor_id': r[6]
	  } for r in res]

def json_analysis(analysis):
	"""" Dump an analysis object to JSON for compilation.
	This requires querying the PredictorEvents to get all events for all runs
	and predictors. This function is somewhat slow due to the overhead of
	creating Python objects (and dumping through Marshmallow), tens of thousands
	of runs."""
	analysis_json = AnalysisFullSchema().dump(analysis)[0]

	pred_ids = [p.id for p in analysis.predictors]
	run_ids = [r.id for r in analysis.runs]
	pes = PredictorEvent.query.filter(
	    (PredictorEvent.predictor_id.in_(pred_ids)) & \
	    (PredictorEvent.run_id.in_(run_ids)))
	pes_json = dump_pe(pes)

	resources_json = AnalysisResourcesSchema().dump(analysis)[0]

	return analysis_json, pes_json, resources_json

class CompileAnalysisResource(AnalysisBaseResource):
	@doc(summary='Compile and lock analysis.')
	@owner_required
	def post(self, analysis):
		analysis.status = 'SUBMITTING'
		analysis.compile_traceback = ''
		db.session.add(analysis)
		db.session.commit()
		task = celery_app.send_task('workflow.compile',
				args=[*json_analysis(analysis),
				analysis.dataset.local_path])
		analysis.celery_id = task.id
		analysis.status = 'PENDING'
		db.session.add(analysis)
		db.session.commit()

		return analysis

class AnalysisStatusResource(AnalysisBaseResource):
	@marshal_with(AnalysisCompiledSchema)
	@doc(summary='Check if analysis has compiled.')
	@fetch_analysis
	def get(self, analysis):
		return analysis

class AnalysisFullResource(AnalysisBaseResource):
	@marshal_with(AnalysisFullSchema)
	@doc(summary='Get analysis (including nested fields).')
	@fetch_analysis
	def get(self, analysis):
		return analysis

class AnalysisResourcesResource(AnalysisBaseResource):
	@marshal_with(AnalysisResourcesSchema)
	@doc(summary='Get analysis resources.')
	@fetch_analysis
	def get(self, analysis):
		return analysis

class AnalysisBundleResource(MethodResource):
	@doc(tags=['analysis'], summary='Get analysis tarball bundle.',
	responses={"200": {
		"description": "gzip tarball, including analysis, resources and events.",
		"type": "application/x-tar"}})
	@fetch_analysis
	def get(self, analysis):
		if (analysis.status != "PASSED" or analysis.bundle_path is None or \
		not exists(analysis.bundle_path)):
			msg = "Analysis bundle not available. Try compiling."
			abort(404, msg)
		return send_file(analysis.bundle_path, as_attachment=True)
