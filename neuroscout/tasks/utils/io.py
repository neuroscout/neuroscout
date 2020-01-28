""" utils """
import json
import tarfile
from pathlib import Path
from grabbit.extensions.writable import build_path
from ...utils.db import put_record, dump_predictor_events
from ...models import Analysis
from ...schemas.analysis import AnalysisFullSchema, AnalysisResourcesSchema

REPORT_PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_'
                '[acq-{acquisition}_][run-{run}_]{type}.{extension}']


def update_record(model, exception=None, **fields):
    if exception is not None:
        k = None
        if 'traceback' in fields:
            k = 'traceback'
        elif 'compile_traceback' in fields:
            k = 'compile_traceback'
        if k:
            fields[k] = f"{fields[k]}.\n{str(exception)}"
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


class PathBuilder():
    def __init__(self, outdir, domain, hash, entities):
        self.outdir = outdir
        prepend = "https://" if "neuroscout.org" in domain else "http://"
        self.domain = prepend + domain
        self.hash = hash
        self.entities = entities

    def build(self, type, extension):
        file = build_path(
            {**self.entities, 'type': type, 'extension': extension},
            path_patterns=REPORT_PATHS)
        outfile = str(self.outdir / file)

        return outfile, '{}/reports/{}/{}'.format(self.domain, self.hash, file)


def analysis_to_json(analysis_id, run_id=None):
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

    pes = dump_predictor_events(
        [(p['id']) for p in analysis_json['predictors']],
        run_id
        )

    dataset_path = Path(analysis.dataset.local_path)
    preproc_path = dataset_path / 'derivatives' / 'fmriprep'

    if preproc_path.exists():
        dataset_path = preproc_path
    return (analysis.id, analysis_json, resources_json, pes,
            str(dataset_path))
