""" Populate database from command line """
import os

from flask_script import Manager
from app import app
from database import db
import json

from bids.grabbids import BIDSLayout
import pandas as pd
import db_utils

from utils import hash_file

app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)
manager = Manager(app)

@manager.command
def add_dataset(bids_path, task):
    from models import (Dataset, Run, Predictor, PredictorEvent,
                        Stimulus, RunStimulus)

    layout = BIDSLayout(bids_path)
    if task not in layout.get_tasks():
        raise ValueError("No such task exists in BIDS dataset.")

    # Extract BIDS dataset info and store in dictionary
    description = json.load(open(
        os.path.join(bids_path, 'dataset_description.json'), 'r'))
    task_description = json.load(open(
        os.path.join(bids_path, 'task-{}_bold.json'.format(task)), 'r'))

    # Get or create dataset model from mandatory arguments
    dataset_model, new = db_utils.get_or_create(db.session, Dataset,
                                                name=description['Name'],
                                                task=task)

    if new:
        dataset_model.task_description = task_description
        dataset_model.description = description
        db.session.commit()
    else:
        print("Dataset already in db")


    # For every run in dataset, add to db if not in
    for run in layout.get(task=task, type='events'):
        print("Processing subject {}, {}".format(run.subject, run.run))
        run_model, new = db_utils.get_or_create(db.session, Run,
                                                subject=run.subject,
                                                number=run.run, task=task,
                                                dataset_id=dataset_model.id)

        if new is False:
            print("Run already in db")
            continue

        # Read event file and extract information
        tsv = pd.read_csv(run.filename, delimiter='\t', index_col=0)
        tsv = dict(tsv.iteritems())
        onsets = tsv.pop('onset')
        durations = tsv.pop('duration')
        stims = tsv.pop('stim_file')

        # # Parse event colums and insert as Predictors
        for col in tsv.keys():
            predictor, _ = db_utils.get_or_create(db.session, Predictor,
                                                    name=col, run_id=run_model.id)

            # Insert each row of Predictor as PredictorEvent
            for i, val in tsv[col].items():
                pe, _ = db_utils.get_or_create(db.session, PredictorEvent,
                                               onset=onsets[i].item(),
                                               duration = durations[i].item(),
                                               value = str(val),
                                               predictor_id=predictor.id)

        # Ingest stimuli
        for i, val in stims.items():
            if val != 'n/a':
                path = os.path.join(bids_path, 'stimuli/{}'.format(val))
                try:
                    stim_hash = hash_file(path)
                except FileNotFoundError:
                    print('Stimulus: {} not found. Skipping.'.format(val))
                    continue

                # Get or create stimulus model
                stimulus_model, new = db_utils.get_or_create(db.session, Stimulus,
                                                             path=path,
                                                             sha1_hash=stim_hash)
                # Get or create Run Stimulus association
                runstim, new = db_utils.get_or_create(db.session, RunStimulus,
                                                      stimulus_id=stimulus_model.id,
                                                      run_id=run_model.id,
                                                      onset=onsets[i].item())

### Add ingestion of Extractors, maybe from json config file ###

if __name__ == '__main__':
    manager.run()
