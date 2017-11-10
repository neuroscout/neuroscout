from app import celery_app
from celery.utils.log import get_task_logger
import pandas as pd
import tarfile
import json
from os.path import join, basename
from tempfile import mkdtemp
from bids.events import BIDSEventCollection
logger = get_task_logger(__name__)

@celery_app.task(name='workflow.compile')
def compile(analysis, resources, predictor_events, bids_dir):
    files_dir = mkdtemp()
    analysis_update = {} # New fields to return for analysis

    # Write out analysis jsons & generate bundle paths
    paths = []
    for obj, name in [(analysis, 'analysis'), (resources, 'resources')]:
        path = join(files_dir, '{}.json'.format(name))
        json.dump(obj, open(path, 'w'))
        paths.append(path)


    # Write out event files
    pes = pd.DataFrame(predictor_events)

    # For each run, make events wide and write out to tempdir
    for run in analysis.pop('runs'):
        ## Write out event files for each run_id
        run_events = pes[pes.run_id==run['id']].drop('run_id', axis=1)

        # Make wide
        run_events = run_events.groupby(
            ['onset', 'duration', 'predictor_id'])['value'].\
            sum().unstack('predictor_id').reset_index()

        # Write out BIDS path
        ses = 'ses-{}_'.format(run['session']) if run.get('session') else ''
        events_fname = join(files_dir,
                            'sub-{}_{}task-{}_run-{}_events.tsv'.format(
            run['subject'], ses, analysis['task_name'], run['number']))
        run_events.to_csv(events_fname, sep='\t', index=False)

    # Transform event files using BIDSEventCollection
    collection = BIDSEventCollection(base_dir=bids_dir)
    collection.read(file_directory=files_dir)

    # Change collection name keys to integers, because inputs come from JSON
    # as such. Could change keys to names to deal with this.
    collection.columns = {int(k):v for k,v in collection.columns.items()}

    for t in analysis['transformations']:
        args = {a['name']:a['value'] for a in t['parameters']}
        collection.apply(t['name'], t['input'], **args)

    # Save out and add to update dictionary
    all_path = join(files_dir, 'all_subjects.tsv')
    collection.write(file=all_path)
    design_matrix = pd.read_csv(all_path, sep='\t').drop('task', axis=1)

    design_matrix.fillna(0, inplace=True)

    tsv_path = join(files_dir, 'events.tsv')
    paths.append(tsv_path)
    design_matrix.to_csv(tsv_path, sep='\t', index=False)


    ### Replace NANs with 0!

    analysis_update['design_matrix'] = design_matrix.to_dict(orient='records')

    # Save bundle as tarball
    bundle_path = '/file-data/analyses/{}_bundle.tar.gz'.format(analysis['hash_id'])
    with tarfile.open(bundle_path, "w:gz") as tar:
        for path in paths:
            tar.add(path, arcname=basename(path))

    analysis_update['bundle_path'] = bundle_path

    return analysis_update
