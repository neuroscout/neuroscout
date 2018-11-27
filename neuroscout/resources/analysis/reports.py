from flask_apispec import doc, use_kwargs, MethodResource, marshal_with
from database import db
from flask import current_app
from sqlalchemy.dialects import postgresql
from models import PredictorEvent, Report
from worker import celery_app
import webargs as wa
from marshmallow import fields
from ..utils import owner_required, abort, fetch_analysis
from .schemas import (AnalysisFullSchema, AnalysisResourcesSchema, ReportSchema,
                      AnalysisCompiledSchema)
import celery.states as states
from utils import put_record
import datetime

def dump_pe(pes):
	""" Serialize PredictorEvents, with *SPEED*, using core SQL.
	Warning: relies on attributes being in correct order. """
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

def jsonify_analysis(analysis, run_id=None):
	"""" Serialize to JSON analysis's predictor events
	Queries PredictorEvents to get all events for all runs and predictors. """



	analysis_json = AnalysisFullSchema().dump(analysis)[0]
	pred_ids = [p['id'] for p in analysis_json['predictors']]
	all_runs = [r['id'] for r in analysis_json['runs']]

	if run_id is None:
		run_id = all_runs
	if not set(run_id) <= set(all_runs):
		raise ValueError("Incorrect run id specified")

	pes = PredictorEvent.query.filter(
	    (PredictorEvent.predictor_id.in_(pred_ids)) & \
	    (PredictorEvent.run_id.in_(run_id)))

	return analysis_json, dump_pe(pes)

@doc(tags=['analysis'])
@marshal_with(AnalysisCompiledSchema)
class CompileAnalysisResource(MethodResource):
	@doc(summary='Compile and lock analysis.')
	@owner_required
	def post(self, analysis):
		put_record(
			{'status': 'SUBMITTING', 'submitted_at': datetime.datetime.utcnow()},
			analysis)

		try:
			task = celery_app.send_task(
					'workflow.compile',
					args=[*jsonify_analysis(analysis),
					AnalysisResourcesSchema().dump(analysis)[0],
					analysis.dataset.local_path, None]
					)
		except:
			put_record(
				{'status': 'FAILED', 'compile_traceback': "Submitting failed. Perhaps analysis is too large?"},
				analysis)

		put_record({'status': 'PENDING', 'compile_task_id': task.id}, analysis)

		return analysis

	@doc(summary='Check if analysis compilation status.')
	@fetch_analysis
	def get(self, analysis):
		return analysis

@marshal_with(ReportSchema)
@use_kwargs({
	'run_id': wa.fields.DelimitedList(fields.Int(),
                                    description='Run id(s).')
}, locations=['query'])
@doc(tags=['analysis'])
class ReportResource(MethodResource):
	@doc(summary='Generate analysis reports.')
	@owner_required
	def post(self, analysis, run_id=None):
		# Submit report generation
		analysis_json, pes_json = jsonify_analysis(analysis, run_id=run_id)

		task = celery_app.send_task('workflow.generate_report',
				args=[analysis_json, pes_json,
				analysis.dataset.local_path, run_id,
				current_app.config['SERVER_NAME']])

		# Create new Report
		report = Report(
			analysis_id=analysis.hash_id,
			runs=run_id,
			task_id=task.id
		)
		db.session.add(report)
		db.session.commit()

		return report

	@doc(summary='Get analysis reports.')
	@fetch_analysis
	def get(self, analysis, run_id=None):
		filters = {'analysis_id': analysis.hash_id}
		if run_id is not None:
			filters['runs'] = run_id

		candidate = Report.query.filter_by(**filters)
		if candidate.count() == 0:
			abort(404, "Report not found")

		report = candidate.filter_by(
			generated_at=max(candidate.with_entities('generated_at'))).one()

		if report.generated_at < analysis.modified_at:
			abort(404, "No fresh reports available")

		if report.status == 'PENDING':
			res = celery_app.AsyncResult(report.task_id)
			if res.state == states.FAILURE:
				put_record(
					{'status': 'FAILED', 'traceback': res.traceback}, report)
			elif res.state == states.SUCCESS:
				put_record(
					{'status': 'OK', 'result': res.result}, report)

		return report
