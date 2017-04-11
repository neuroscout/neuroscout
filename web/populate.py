""" Populate database from command line """
import os
import re
import json
import pandas as pd

from flask_script import Manager
from app import app
from database import db
import db_utils
from utils import hash_file, hash_str

from resources.extractor import ExtractorSchema

from bids.grabbids import BIDSLayout
from bids.transform import BIDSEventCollection
from pliers.stimuli import load_stims
from pliers.graph import Graph

from models import (Dataset, Run, Predictor, PredictorEvent,
                    Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent)

app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)
manager = Manager(app)


@manager.command
def add_dataset(bids_path, task, replace=False, **kwargs):
    """ Adds a BIDS dataset task to the database """
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
    for run_events in layout.get(task=task, type='events', **kwargs):
        print("Processing subject {}, run {}".format(
            run_events.subject, run_events.run))
        run_model, new = db_utils.get_or_create(db.session, Run,
                                                subject=run_events.subject,
                                                number=run_events.run, task=task,
                                                dataset_id=dataset_model.id)

        if new is False and replace is False:
            print("Run already in db, skipping...")
            continue

        # Read event file and extract information
        tsv = pd.read_csv(run_events.filename, delimiter='\t')
        tsv = dict(tsv.iteritems())
        onsets = tsv.pop('onset')
        durations = tsv.pop('duration')
        stims = tsv.pop('stim_file')

        # Parse event columns and insert as Predictors
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

@manager.command
def add_user(email, password):
    from models import user_datastore
    from flask_security.utils import encrypt_password

    user_datastore.create_user(email=email, password=encrypt_password(password))
    db.session.commit()

@manager.command
def add_extractors(path_json):
    es = ExtractorSchema()

    for extractor in json.load(open(path_json, 'r')):
        new, errors = es.load(extractor)

        if errors:
        	raise Exception("Error parsing extractor")
        else:
        	db.session.add(new)
        	db.session.commit()

    es = ExtractorSchema()

@manager.command
def extract_features(bids_path, graph_spec, **kwargs):
    # Load event files
    collection = BIDSEventCollection(bids_path)
    collection.read(**kwargs)

    # Filter to only get stim files
    stim_pattern = 'stim_file/(.*)'
    stims = [re.findall(stim_pattern, col)[0]
     for col in collection.columns
     if re.match(stim_pattern, col)]

    # Get absolute path and load
    stims = load_stims(
        [os.path.join(bids_path, 'stimuli', s) for s in stims])

    # Construct and run the graph
    graph = Graph(spec=graph_spec)
    results = graph.run(stims, merge=False)

    # For every extracted feature
    for res in results:
        # Hash extractor name + feature name
        ef_hash = hash_str(str(res.extractor.__hash__()) + res.features[0])

        # Get or create feature
        ef_model, _ = db_utils.get_or_create(db.session,
                                             ExtractedFeature,
                                             sha1_hash=ef_hash,
                                             extractor_name=res.extractor.name,
                                             feature_name=res.features[0])

        # Get associated stimulus record
        stim_hash = hash_file(res.stim.filename)
        stimulus = db.session.query(Stimulus).filter_by(sha1_hash=stim_hash).one()

        if not stimulus:
            raise Exception("No stim found!")

        # Set onset for event
        onset = None if pd.isnull(res.onsets) else res.onsets[0]
        # Get or create ExtractedEvent
        ee_model, _ = db_utils.get_or_create(db.session,
                                               ExtractedEvent,
                                               commit=False,
                                               onset=onset,
                                               stimulus_id=stimulus.id,
                                               ef_id=ef_model.id)

        ## Add data to it
        ee_model.value = res.data[0][0]
        if not pd.isnull(res.durations):
            ee_model.duration = res.durations[0]
        ee_model.history = res.history.string

        db.session.commit()


if __name__ == '__main__':
    manager.run()
