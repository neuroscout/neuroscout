from neuroscout.models import Analysis, PredictorEvent
from neuroscout.resources.analysis.predictor import dump_pe
from neuroscout.resources.analysis.schemas import (AnalysisFullSchema,
                                                   AnalysisResourcesSchema)


def dump_analysis(analysis_id, run_id=None):
    """" Serialize analysis and related PredictorEvents to JSON.
    Queries PredictorEvents to get all events for all runs and predictors. """

    # Query for analysis
    analysis = Analysis.query.filter_by(hash_id=analysis_id).one()

    # Dump analysis JSON
    analysis_json = AnalysisFullSchema().dump(analysis)[0]
    resources_json = AnalysisResourcesSchema().dump(analysis)[0]

    # Query and dump PredictorEvents
    pred_ids = [p['id'] for p in analysis_json['predictors']]
    all_runs = [r['id'] for r in analysis_json['runs']]

    if run_id is None:
        run_id = all_runs
    if not set(run_id) <= set(all_runs):
        raise ValueError("Incorrect run id specified")

    pes = PredictorEvent.query.filter(
        (PredictorEvent.predictor_id.in_(pred_ids)) &
        (PredictorEvent.run_id.in_(run_id)))

    return (analysis.id, analysis_json, resources_json, dump_pe(pes),
            analysis.dataset.local_path)
