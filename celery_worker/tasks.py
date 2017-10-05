from app import celery_app
from celery.utils.log import get_task_logger
import pandas as pd
from os.path import join
from tempfile import mkdtemp
from bids.events import BIDSEventCollection
logger = get_task_logger(__name__)

@celery_app.task(name='workflow.compile')
def compile(analysis, predictor_events, bids_dir):
    # Write out event files
    pes = pd.DataFrame(predictor_events)
    files_dir = mkdtemp()

    analysis_update = {}

    # For each run, make events wide and write out to tempdir
    for run in analysis.pop('runs'):
        ## Write out event files for each run_id
        run_events = pes[pes.run_id==run['id']].drop('run_id', axis=1)

        # Make wide
        run_events = run_events.groupby(['onset', 'duration', 'predictor_id'])['value'].\
            sum().unstack('predictor_id').reset_index()

        ses = 'ses-{}_'.format(run['session']) if run.get('session') else ''

        events_fname = join(files_dir,
                            'sub-{}_{}task-{}_run-{}_events.tsv'.format(
            run['subject'], ses, analysis['task_name'], run['number']))

        run_events.to_csv(events_fname, sep='\t', index=False)

    # Transform event files using BIDSEventCollection
    collection = BIDSEventCollection(base_dir=bids_dir)
    collection.read(file_directory=files_dir)

    for t in analysis['transformations']:
        args = {a['name']:a['value'] for a in t['parameters']}
        collection.apply(t['name'], [str(i) for i in t['input']],
                               **args)

    # Save out and add to update dictionary
    all_path = join(files_dir, 'all_subjects.tsv')
    collection.write(file=all_path)
    design_matrix = pd.read_csv(all_path, sep='\t').drop('task', axis=1)

    analysis_update['design_matrix'] = design_matrix.to_dict(orient='records')

    return analysis_update
