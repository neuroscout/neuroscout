""" utils """
import json
import tarfile
from ..utils.db import put_record, dump_pe
from ..models import Analysis, PredictorEvent, Predictor, RunStimulus
from ..schemas.analysis import AnalysisFullSchema, AnalysisResourcesSchema


def update_record(model, exception=None, **fields):
    if exception is not None:
        if 'traceback' in fields:
            fields['traceback'] = f"{fields['traceback']}. \
             Error:{str(exception)}"
        if 'status' not in fields:
            fields['status'] = 'FAILED'
    put_record(fields, model)
    return fields


def write_jsons(objects, base_dir):
    """ Write JSON objects to file
    Args:
        objects (list of tuples) Pairs of JSON-objects and base file name
        base_dir: Path-like directory to write to
    Returns:
        string path, base_name
    """
    results = []
    for obj, file_name in objects:
        path = (base_dir / file_name).with_suffix('.json')
        json.dump(obj, path.open('w'))
        results.append((str(path), path.name))
    return results


def write_tarball(paths, filename):
    """ Write tarball of files in paths
    Args:
        paths (list): list of file paths to include
        filename (str): full path name of tarball
    """
    with tarfile.open(filename, "w:gz") as tar:
        for path, arcname in paths:
            tar.add(path, arcname=arcname)


def create_pes(predictors, run_ids):
    """ Create PredictorEvents from EFs """
    for pred in predictors:
        ef = pred.extracted_feature
        all_pes = []
        # For all instances for stimuli in this task's runs
        for ee in ef.extracted_events:
            # if ee.value:
            query = RunStimulus.query.filter_by(stimulus_id=ee.stimulus_id)
            if run_ids is not None:
                query = query.filter(RunStimulus.run_id.in_(run_ids))
            for rs in query:
                duration = ee.duration
                if duration is None:
                    duration = rs.duration
                all_pes.append(
                    dict(
                        onset=(ee.onset or 0) + rs.onset,
                        value=ee.value,
                        object_id=ee.object_id,
                        duration=duration,
                        predictor_id=pred.id,
                        run_id=rs.run_id,
                        stimulus_id=ee.stimulus_id
                    )
                )


def dump_analysis(analysis_id, run_id=None):
    """" Serialize analysis and related PredictorEvents to JSON.
    Queries PredictorEvents to get all events for all runs and predictors. """

    # Query for analysis
    analysis = Analysis.query.filter_by(hash_id=analysis_id).one()

    # Dump analysis JSON
    analysis_json = AnalysisFullSchema().dump(analysis)[0]
    resources_json = AnalysisResourcesSchema().dump(analysis)[0]

    # Get run IDs
    all_runs = [r['id'] for r in analysis_json['runs']]
    if run_id is None:
        run_id = all_runs
    if not set(run_id) <= set(all_runs):
        raise ValueError("Incorrect run id specified")

    # Query and dump PredictorEvents
    all_pred_ids = [(p['id']) for p in analysis_json['predictors']]
    all_preds = Predictor.query.filter(Predictor.id.in_(all_pred_ids))

    base_pred_ids = [p.id for p in all_preds.filter_by(ef_id=None)]
    ext_preds = Predictor.query.filter(
        Predictor.id.in_(set(all_pred_ids) - set(base_pred_ids)))

    pes = PredictorEvent.query.filter(
        (PredictorEvent.predictor_id.in_(base_pred_ids)) &
        (PredictorEvent.run_id.in_(run_id)))
    pes = dump_pe(pes)

    pes += create_pes(ext_preds, run_id)

    return (analysis.id, analysis_json, resources_json, dump_pe(pes),
            analysis.dataset.local_path)
