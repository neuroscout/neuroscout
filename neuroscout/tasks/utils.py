""" utils """
import json
import tarfile
from ..utils.db import put_record, dump_pe
from ..models import Analysis, PredictorEvent
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
