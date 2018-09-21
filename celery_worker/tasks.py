import tarfile
import json
import pandas as pd
from collections import defaultdict
from pathlib import Path
from tempfile import mkdtemp
from bids.analysis import Analysis
from bids.layout import BIDSLayout
from grabbit import Layout
from copy import deepcopy
from celery.contrib import rdb
from celery.utils.log import get_task_logger
from app import celery_app

logger = get_task_logger(__name__)
PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_[acq-{acquisition}_][run-{run}_]events.tsv']
REPORT_PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_[acq-{acquisition}_][run-{run}_]{type}.{extension}']

def _get_entities(run):
    """ Get BIDS-entities from run object """
    entities = {
        r:v
        for r,v in run.items()
        if r in ['number', 'session', 'subject', 'acquisition'] and v is not None
        }

    if 'number' in entities:
        entities['run'] = entities.pop('number')
    return entities

def _writeout_events(analysis, pes, outdir):
    """ Writeout predictor_events into BIDS event files """
    gl = Layout(str(outdir))
    outdir = outdir / "func"
    outdir.mkdir(exist_ok=True)

    desc = {'Name': 'Events', 'BIDSVersion': '1.0'}
    json.dump(desc, (outdir / 'dataset_description.json').open('w'))
    # Load events and rename columns to human-readable
    pes = pd.DataFrame(pes)
    predictor_names = {p['id']:p['name'] for p in analysis['predictors']}
    pes.predictor_id = pes.predictor_id.map(predictor_names)

    # Write out event files
    paths = []
    for run in analysis.get('runs'):
        # Write out event files for each run_id
        run_events = pes[pes.run_id==run['id']].drop('run_id', axis=1)
        entities = _get_entities(run)
        entities['task'] = analysis['task_name']

        if run_events.empty is False:
            for name, df in run_events.groupby('predictor_id'):
                df_col = df.groupby(['onset', 'duration'])['value'].max()
                df_col = df_col.reset_index().rename(columns={'value': name})

                # Write out BIDS path
                fname = outdir / name / gl.build_path(entities, path_patterns=PATHS)
                fname.parent.mkdir(exist_ok=True)
                paths.append((fname.as_posix(), 'events/{}/{}'.format(name,fname.name)))
                df_col.to_csv(fname, sep='\t', index=False)

    return paths

def _merge_dictionaries(*arg):
    """ Set merge dictionaries """
    dd = defaultdict(set)

    for d in arg: # you can list as many input dicts as you want here
        for key, value in d.items():
            dd[key].add(value)
    return dict(((k, list(v)) if len(v) > 1 else (k, list(v)[0])
                 for k, v in dd.items()))


def _build_analysis(analysis, predictor_events, bids_dir, run_id=None):
    tmp_dir = Path(mkdtemp())

    entities = [{}]
    if run_id is not None:
        # Get entities of runs, and add to kwargs
        for rid in run_id:
            for run in analysis['runs']:
                if rid == run['id']:
                    entities.append(_get_entities(run))
                    break

    entities = _merge_dictionaries(*entities)
    entities['scan_length'] = max([r['duration'] for r in analysis['runs']])
    entities['task'] = analysis['task_name']

    # Write out all events
    paths = _writeout_events(analysis, predictor_events, tmp_dir)
    # Load events and try applying transformations

    bids_layout = BIDSLayout(
        [(bids_dir, 'bids'), (str(tmp_dir), ['bids', 'derivatives'])])
    bids_analysis = Analysis(
        bids_layout, deepcopy(analysis.get('model')))
    bids_analysis.setup(**entities)

    return tmp_dir, paths, bids_analysis

@celery_app.task(name='workflow.compile')
def compile(analysis, predictor_events, resources, bids_dir, run_ids):
    tmp_dir, bundle_paths, bids_analysis = _build_analysis(
        analysis, predictor_events, bids_dir, run_ids)

    sidecar = {"RepetitionTime": analysis['TR']}
    # Write out JSON files
    for obj, name in [
        (analysis, 'analysis'),
        (resources, 'resources'),
        (analysis.get('model'), 'model'),
        (sidecar, 'task-{}_bold'.format(analysis['task_name']))]:

        path = (tmp_dir / name).with_suffix('.json')
        json.dump(obj, path.open('w'))
        bundle_paths.append((path.as_posix(), path.name))

    # Save bundle as tarball
    bundle_path = '/file-data/analyses/{}_bundle.tar.gz'.format(analysis['hash_id'])
    with tarfile.open(bundle_path, "w:gz") as tar:
        for path, arcname in bundle_paths:
            tar.add(path, arcname=arcname)

    return {'bundle_path': bundle_path}

def _format_url(domain, hash_id, file):
    return '{}/reports/{}/{}'.format(domain, hash_id, file)

@celery_app.task(name='workflow.generate_report')
def generate_report(analysis, predictor_events, bids_dir, run_ids, domain):
    _, _, bids_analysis = _build_analysis(
        analysis, predictor_events, bids_dir, run_ids)
    outdir = Path('/file-data/reports') / analysis['hash_id']
    outdir.mkdir(exist_ok=True)
    gl = Layout(str(outdir))

    first_level = bids_analysis.blocks[0]

    dm_urls = []
    for dm in first_level.get_design_matrix():
        # Writeout design matrix
        out = gl.build_path(
            {**dm.entities,
             'type':'design_matrix', 'extension':'tsv'},
            path_patterns=REPORT_PATHS)
        dm.dense.to_csv(str(outdir / out))
        logger.info(str(outdir / out))
        dm_urls.append(_format_url(domain, analysis['hash_id'], out))

    return {'design_matrix': dm_urls}
