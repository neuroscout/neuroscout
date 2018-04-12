from app import celery_app
from celery.utils.log import get_task_logger
import pandas as pd
import tarfile
import json
from pathlib import Path
from tempfile import mkdtemp
from bids.analysis import Analysis
from bids.grabbids import BIDSLayout
from celery.contrib import rdb

logger = get_task_logger(__name__)


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
        run_events = pes[pes.run_id==run['id']].drop('run_id', axis=1)

        if run_events.empty is False:
            # Make wide
            run_events = run_events.groupby(
                ['onset', 'duration', 'predictor_id'])['value'].\
                sum().unstack('predictor_id').reset_index()

            print(run_events.columns)

            # Write out BIDS path
            ses = 'ses-{}_'.format(run['session']) if run.get('session') else ''
            events_fname = outdir / 'sub-{}_{}task-{}_run-{}_events.tsv'.format(
                run['subject'], ses, analysis['task_name'], run['number'])
            paths.append(events_fname)
            run_events.to_csv(events_fname, sep='\t', index=False)

    return paths

@celery_app.task(name='workflow.compile')
def compile(analysis, predictor_events, resources, bids_dir):
    files_dir = Path(mkdtemp())
    model = analysis.pop('model')
    scan_length = analysis['runs'][0]['duration']

    # Get run entities
    entities = {'session': [], 'subject': [], 'number': []}
    for ent, entries in entities.items():
        for r in analysis['runs']:
            if r[ent]:
             entries += [r[ent]]
    entities = {k:v for k,v in entities.items() if v}
    entities['run'] = [int(r) for r in entities.pop('number')]

    # Write out events
    bundle_paths = writeout_events(analysis, predictor_events, files_dir)

    # Load events and try applying transformations
    bids_layout = BIDSLayout([bids_dir, files_dir.as_posix()])
    bids_analysis = Analysis(bids_layout, model)
    bids_analysis.setup(derivatives='only', task=analysis['task_name'], scan_length=scan_length, **entities)

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
