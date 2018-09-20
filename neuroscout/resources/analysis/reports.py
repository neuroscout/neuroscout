from flask_apispec import doc
from database import db
from sqlalchemy.dialects import postgresql
from models import PredictorEvent
from worker import celery_app

from .endpoints import AnalysisMethodResource
from ..utils import owner_required
from .schemas import AnalysisFullSchema, AnalysisResourcesSchema


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

def json_pes(analysis_json, run_id=None):
	"""" Serialize to JSON and analysis's predictor events
	This requires querying the PredictorEvents to get all events for all runs
	and predictors.
    """
	pred_ids = [p['id'] for p in analysis_json['predictors']]
	run_ids = [r['id'] for r in analysis_json['runs']]

	if run_id is not None:
		if run_id not in run_ids:
			raise ValueError("Incorrect run id specified")
		run_ids = [run_id]

	pes = PredictorEvent.query.filter(
	    (PredictorEvent.predictor_id.in_(pred_ids)) & \
	    (PredictorEvent.run_id.in_(run_ids)))
	pes_json = dump_pe(pes)

	return pes_json

class CompileAnalysisResource(AnalysisMethodResource):
    @doc(summary='Compile and lock analysis.')
    @owner_required
    def post(self, analysis):
        analysis.status = 'SUBMITTING'
        analysis.compile_traceback = ''
        db.session.add(analysis)
        db.session.commit()

        analysis_json = AnalysisFullSchema().dump(analysis)[0]
        resources_json = AnalysisResourcesSchema().dump(analysis)[0]
        pes_json = json_pes(analysis_json)
        task = celery_app.send_task('workflow.compile',
        		args=[analysis_json, pes_json, resources_json,
        		analysis.dataset.local_path])
        analysis.compile_task_id = task.id
        analysis.status = 'PENDING'
        db.session.add(analysis)
        db.session.commit()

        return analysis
