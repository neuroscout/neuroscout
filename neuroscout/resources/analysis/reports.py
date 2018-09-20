from flask_apispec import doc, use_kwargs
from database import db
from sqlalchemy.dialects import postgresql
from models import PredictorEvent
from worker import celery_app
import webargs as wa
from marshmallow import fields
from .endpoints import AnalysisMethodResource
from ..utils import owner_required
from .schemas import AnalysisFullSchema, AnalysisResourcesSchema


def dump_pe(pes):
	""" Custom function to serialize PredictorEvent, build for *SPEED*
	Uses Core SQL queries. Relies on attributes being in correct order. """
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

def json_pes(analysis_json, run_id=None):
	"""" Serialize to JSON analysis's predictor events
	Queries PredictorEvents to get all events for all runs and predictors. """
	pred_ids = [p['id'] for p in analysis_json['predictors']]
	all_runs = [r['id'] for r in analysis_json['runs']]

	if run_id is None:
		run_id = all_runs
	if not set(run_id) <= set(all_runs):
		raise ValueError("Incorrect run id specified")

	pes = PredictorEvent.query.filter(
	    (PredictorEvent.predictor_id.in_(pred_ids)) & \
	    (PredictorEvent.run_id.in_(run_id)))

	return dump_pe(pes)

class CompileAnalysisResource(AnalysisMethodResource):
	@doc(summary='Compile and lock analysis.')
	@use_kwargs({
		'run_id': wa.fields.DelimitedList(fields.Int(),
	                                    description='Run id(s).')
	}, locations=['query'])
	@owner_required
	def post(self, analysis, run_id=None):
		analysis.status = 'SUBMITTING'
		analysis.compile_traceback = ''
		db.session.add(analysis)
		db.session.commit()

		analysis_json = AnalysisFullSchema().dump(analysis)[0]
		resources_json = AnalysisResourcesSchema().dump(analysis)[0]
		pes_json = json_pes(analysis_json) # Send PEs for all runs

		task = celery_app.send_task('workflow.compile',
				args=[analysis_json, pes_json, resources_json,
				analysis.dataset.local_path, run_id])
		analysis.compile_task_id = task.id
		analysis.status = 'PENDING'
		db.session.add(analysis)
		db.session.commit()

		return analysis
