from app import celery_app
from celery.utils.log import get_task_logger
import pandas as pd
import tarfile
import json
from pathlib import Path
from tempfile import mkdtemp
from bids.analysis import Analysis
from bids.variables import SparseRunVariable
from bids.variables.entities import RunInfo
from bids.grabbids import BIDSLayout
from celery.contrib import rdb

logger = get_task_logger(__name__)


def get_events_path(entities, task_name):
    ses = 'ses-{}_'.format(entities['session']) if entities.get('session') else ''
    run_num = 'run-{}_'.format(entities['number']) if entities.get('number') else ''
    fname = 'sub-{}_{}task-{}_{}events.tsv'.format(
        entities['subject'], ses, task_name, run_num)

    return fname

def writeout_events(analysis, pes, outdir):
    """ Write event files from JSON """
    outdir = outdir / "func"
    outdir.mkdir(exist_ok=True)

    # Load events and rename columns to human-readable
    pes = pd.DataFrame(pes)
    predictor_names = {di["id"]: di["name"] for di in analysis['predictors']}
    pes.predictor_id = pes.predictor_id.map(predictor_names)
    # Write out event files

    paths = []
    for run in analysis.pop('runs'):
        ## Write out event files for each run_id
        run_events = pes[pes.run_id==run['id']].drop('run_id', axis=1).rename(
            columns={'value': 'amplitude'})

        entities = {r:v for r,v in run.items()
                    if r in ['number', 'session', 'subject'] and v is not None}
        if 'number' in entities:
            entities['run'] = entities.pop('number')

        run_info = RunInfo(entities=entities,
                           duration=run_events['duration'],
                           tr=None, image=None)

        if run_events.empty is False:
            dfs = []
            for name, df in run_events.groupby('predictor_id'):
                max_val = df.groupby(['onset', 'duration'])['amplitude'].max().reset_index()

                variable = SparseRunVariable(name, max_val, run_info, 'events')

                ## TODO: Only up sample variables to convert nas to 0
                df = variable.to_dense(2).to_df()
                df['condition'] = name
                dfs.append(df)

            dfs = pd.concat(dfs)
            dfs['amplitude'] = dfs['amplitude'].astype('float')
            dfs = dfs.pivot_table(index=['onset', 'duration'], values='amplitude',
                            columns=['condition']).reset_index()

            # Write out BIDS path
            fname = outdir / get_events_path(entities, analysis['task_name'])
            paths.append(fname)
            dfs.to_csv(fname, sep='\t', index=False)

    return paths

@celery_app.task(name='workflow.compile')
def compile(analysis, predictor_events, resources, bids_dir):
    files_dir = Path(mkdtemp())
    model = analysis.pop('model')
    scan_length = analysis['runs'][0]['duration']

    subject = [model['input']['subject'][0]]

    # Write out events
    bundle_paths = writeout_events(analysis, predictor_events, files_dir)

    # Load events and try applying transformations
    bids_layout = BIDSLayout(bids_dir, config=[('bids', [bids_dir, files_dir.as_posix()])])
    bids_analysis = Analysis(bids_layout, model)
    bids_analysis.setup(derivatives='only', task=analysis['task_name'],
                        scan_length=scan_length, subject=subject)

    # Write out analysis & resource JSON
    for obj, name in [(analysis, 'analysis'), (resources, 'resources'), (model, 'model')]:
        path = (files_dir / name).with_suffix('.json')
        json.dump(obj, path.open('w'))
        bundle_paths.append(path)

    # Save bundle as tarball
    bundle_path = '/file-data/analyses/{}_bundle.tar.gz'.format(analysis['hash_id'])
    with tarfile.open(bundle_path, "w:gz") as tar:
        for path in bundle_paths:
            tar.add(path.as_posix(), arcname=path.name)

    return {'bundle_path': bundle_path}
