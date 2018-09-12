from app import celery_app
from celery.utils.log import get_task_logger
import pandas as pd
import tarfile
import json
from pathlib import Path
from tempfile import mkdtemp
from bids.analysis import Analysis
from bids.layout import BIDSLayout
from grabbit import Layout
from copy import deepcopy

logger = get_task_logger(__name__)
PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_[acq-{acquisition}_][run-{run}_]events.tsv']

def writeout_events(analysis, pes, outdir):
    """ Write event files from JSON """
    gl = Layout(outdir.as_posix())
    outdir = outdir / "func"
    outdir.mkdir(exist_ok=True)

    desc = {"Name": "Events", "BIDSVersion": "1.0"}
    json.dump(desc, (outdir / 'dataset_description.json').open('w'))

    # Load events and rename columns to human-readable
    pes = pd.DataFrame(pes)
    predictor_names = {di["id"]: di["name"] for di in analysis['predictors']}
    pes.predictor_id = pes.predictor_id.map(predictor_names)

    # Write out event files
    paths = []
    for run in analysis.pop('runs'):
        # Write out event files for each run_id
        run_events = pes[pes.run_id==run['id']].drop('run_id', axis=1)

        run['run'] = run.pop('number')
        entities = {r:v for r,v in run.items()
                    if r in ['run', 'session', 'subject', 'acquisition'] and v is not None}
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

@celery_app.task(name='workflow.compile')
def compile(analysis, predictor_events, resources, bids_dir):
    files_dir = Path(mkdtemp())
    model = analysis.pop('model')

    kwargs = {'scan_length': analysis['runs'][0]['duration'],
              'subject': [model['input']['subject'][0]],
              'task': analysis['task_name']}
    if 'run' in model['input']:
        kwargs['run'] = model['input']['run'][0]

    # Write out events
    bundle_paths = writeout_events(analysis, predictor_events, files_dir)
    logger.info(model['input'])
    # Load events and try applying transformations
    bids_layout = BIDSLayout([(bids_dir, 'bids'), (files_dir.as_posix(), 'derivatives')])
    bids_analysis = Analysis(bids_layout, deepcopy(model))
    bids_analysis.setup(**kwargs)

    # Sidecar:
    sidecar = {"RepetitionTime": analysis['TR']}

    # Write out analysis & resource JSON
    for obj, name in [(analysis, 'analysis'), (resources, 'resources'),
                      (model, 'model'), (sidecar, 'task-{}_bold'.format(analysis['task_name']))]:
        path = (files_dir / name).with_suffix('.json')
        json.dump(obj, path.open('w'))
        bundle_paths.append((path.as_posix(), path.name))

    # Save bundle as tarball
    bundle_path = '/file-data/analyses/{}_bundle.tar.gz'.format(analysis['hash_id'])
    with tarfile.open(bundle_path, "w:gz") as tar:
        for path, arcname in bundle_paths:
            tar.add(path, arcname=arcname)

    return {'bundle_path': bundle_path}
