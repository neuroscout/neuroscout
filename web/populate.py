""" Functions to populate database from datasets and extracted features """
import os
import re
import json
import pandas as pd

import db_utils
from utils import hash_file, hash_str

from bids.grabbids import BIDSLayout
from bids.transform import BIDSEventCollection
from pliers.stimuli import load_stims
from pliers.graph import Graph

from models import (Dataset, Run, Predictor, PredictorEvent,
                    Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent)

import magic
import nibabel as nib

def add_dataset(session, bids_path, task, replace=False, verbose=True, **kwargs):
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
    dataset_model, new = db_utils.get_or_create(session, Dataset,
                                                name=description['Name'])

    if new:
        dataset_model.description = description
        session.commit()
    else:
        print("Dataset already in db")

    # For every run in dataset, add to db if not in
    for run_events in layout.get(task=task, type='events', **kwargs):
        if verbose:
            print("Processing subject {}, run {}".format(
                run_events.subject, run_events.run))

        # Get entities

        entities = {entity : getattr(run_events, entity)
                    for entity in ['session', 'task', 'subject']
                    if entity in run_events._fields}
        run_model, new = db_utils.get_or_create(session, Run,
                                                dataset_id=dataset_model.id,
                                                number = run_events.run,
                                                **entities)
        entities['run'] = run_events.run

        if new is False:
            if replace is False:
                if verbose:
                    print("Run already in db, skipping...")
                continue
        else:
            # Get BOLD
            try:
                img = nib.load(layout.get(type='bold', extensions='.nii.gz',
                                  return_type='file',
                                  **entities)[0])
                run_model.duration = img.shape[3] * img.header.get_zooms()[-1] / 1000
            except (nib.filebasedimages.ImageFileError, IndexError) as e:
                print("Error loading BOLD file, duration not loaded.")

            run_model.task_description = task_description
            run_model.TR = task_description['RepetitionTime']

            preprocs = layout.get(type='preproc', return_type='file',
                                  **entities)
            try:
                mni = [re.findall('derivatives.*MNI152.*', pre)
                           for pre in preprocs
                           if re.findall('derivatives.*MNI152.*', pre)]
                run_model.path = [item for sublist in mni for item in sublist][0]
            except IndexError:
                pass

        # Read event file and extract information
        tsv = pd.read_csv(run_events.filename, delimiter='\t')
        tsv = dict(tsv.iteritems())
        onsets = tsv.pop('onset')
        durations = tsv.pop('duration')
        stims = tsv.pop('stim_file')

        # Parse event columns and insert as Predictors
        for col in tsv.keys():
            predictor, _ = db_utils.get_or_create(session, Predictor,
                                                  name=col,
                                                  dataset_id=dataset_model.id)

            # Insert each row of Predictor as PredictorEvent
            for i, val in tsv[col].items():
                pe, _ = db_utils.get_or_create(session, PredictorEvent,
                                               onset=onsets[i].item(),
                                               duration = durations[i].item(),
                                               value = str(val),
                                               predictor_id=predictor.id,
                                               run_id = run_model.id)

        # Ingest stimuli
        mimetypes = set()
        for i, val in stims.items():
            if val != 'n/a':
                path = os.path.join(bids_path, 'stimuli/{}'.format(val))
                name = os.path.basename(path)
                try:
                    stim_hash = hash_file(path)
                    mimetype = magic.from_file(path, mime=True)
                    mimetypes.update([mimetype])
                except FileNotFoundError:
                    if verbose:
                        print('Stimulus: {} not found. Skipping.'.format(val))
                    continue

                # Get or create stimulus model
                stimulus_model, _ = db_utils.get_or_create(session, Stimulus,
                                                           name=name,
                                                           path=path,
                                                           sha1_hash=stim_hash,
                                                           mimetype=mimetype)
                # Get or create Run Stimulus association
                runstim, _ = db_utils.get_or_create(session, RunStimulus,
                                                    stimulus_id=stimulus_model.id,
                                                    run_id=run_model.id,
                                                    onset=onsets[i].item())

    dataset_model.mimetypes = list(mimetypes)
    session.commit()

    return dataset_model.id

def extract_features(session, bids_path, graph_spec,  verbose=True, **kwargs):
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
    ef_model_ids = []
    for res in results:
        extractor = res.extractor
        # Hash extractor name + feature name
        ef_hash = hash_str(str(extractor.__hash__()) + res.features[0])

        # Get or create feature
        ef_model, ef_new = db_utils.get_or_create(session,
                                             ExtractedFeature,
                                             commit=False,
                                             sha1_hash=ef_hash)

        if ef_new:
            ef_model.extractor_name=extractor.name,
            ef_model.feature_name=res.features[0]

            # Save extractor parameters as JSON
            tr_attrs = [getattr(res, attr) for attr in extractor._log_attributes]
            ef_model.extractor_parameters = str(dict(
                zip(extractor._log_attributes, tr_attrs)))
            session.commit()

        ef_model_ids.append(ef_model.id)

        # Get associated stimulus record
        stim_hash = hash_file(res.stim.filename)
        stimulus = session.query(Stimulus).filter_by(sha1_hash=stim_hash).one()

        if not stimulus:
            raise Exception("Stimulus not found in database, have you added"
                            "this dataset to the database?")

        # Set onset for event
        onset = None if pd.isnull(res.onsets) else res.onsets[0]
        # Get or create ExtractedEvent
        ee_model, ee_new = db_utils.get_or_create(session,
                                               ExtractedEvent,
                                               commit=False,
                                               onset=onset,
                                               stimulus_id=stimulus.id,
                                               ef_id=ef_model.id)

        # Add data to it (whether or not its new, as we may want to update)
        ee_model.value = res.data[0][0]
        if not pd.isnull(res.durations):
            ee_model.duration = res.durations[0]
        ee_model.history = res.history.string

        session.commit()

    return ef_model_ids
