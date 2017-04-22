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
                    Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent,
                    GroupPredictor, GroupPredictorValue)

import magic
import nibabel as nib

def add_predictor(session, predictor_name, dataset_id, run_id,
                  onsets, durations, values, **kwargs):
    """" Adds a new Predictor to a run given a set of values
    If Predictor already exist, use that one """
    predictor, _ = db_utils.get_or_create(session, Predictor,
                                          name=predictor_name,
                                          dataset_id=dataset_id,
                                          **kwargs)

    # Insert each row of Predictor as PredictorEvent
    for i, val in enumerate(values):
        pe, _ = db_utils.get_or_create(session, PredictorEvent,
                                       commit=False,
                                       onset=onsets[i],
                                       predictor_id=predictor.id,
                                       run_id = run_id)
        pe.duration = durations[i]
        pe.value = str(val)
        session.commit()

    return predictor.id

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
                                                id=description['Name'])

    if new:
        dataset_model.description = description
        session.commit()
    else:
        if not replace:
            print("Dataset already in db.")
            return dataset_model.id

    """ Parse every Run """
    for run_events in layout.get(task=task, type='events', **kwargs):
        if verbose:
            print("Processing subject {}, run {}".format(
                run_events.subject, run_events.run))

        # Get entities
        entities = {entity : getattr(run_events, entity)
                    for entity in ['session', 'task', 'subject']
                    if entity in run_events._fields}

        """ Extract Run information """
        run_model, new = db_utils.get_or_create(session, Run,
                                                dataset_id=dataset_model.id,
                                                number=run_events.run,
                                                **entities)
        entities['run'] = run_events.run

        # Get BOLD
        try:
            img = nib.load(layout.get(type='bold', extensions='.nii.gz',
                              return_type='file', **entities)[0])
            run_model.duration = img.shape[3] * img.header.get_zooms()[-1] / 1000
        except (nib.filebasedimages.ImageFileError, IndexError) as e:
            print("Error loading BOLD file, duration not loaded.")

        run_model.task_description = task_description
        run_model.TR = task_description['RepetitionTime']

        preprocs = layout.get(type='preproc', return_type='file', **entities)

        try: # Try to get path of preprocessed data
            mni = [re.findall('derivatives.*MNI152.*', pre)
                       for pre in preprocs
                       if re.findall('derivatives.*MNI152.*', pre)]
            run_model.path = [item for sublist in mni for item in sublist][0]
        except IndexError:
            pass
        session.commit()

        """ Extract Predictors"""
        # Read event file and extract information
        tsv = pd.read_csv(run_events.filename, delimiter='\t')
        tsv = dict(tsv.iteritems())
        onsets = tsv.pop('onset').tolist()
        durations = tsv.pop('duration').tolist()
        stims = tsv.pop('stim_file')

        # Parse event columns and insert as Predictors
        for predictor in tsv.keys():
            add_predictor(session, predictor, dataset_model.id, run_model.id,
                          onsets, durations, tsv[predictor].tolist())

        """ Ingest Stimuli """
        mimetypes = set()
        for i, val in stims.items():
            if val != 'n/a':
                base_path = 'stimuli/{}'.format(val)
                path = os.path.join(bids_path, base_path)
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
                                                           commit=False,
                                                           sha1_hash=stim_hash)
                stimulus_model.name=name
                stimulus_model.path=base_path
                stimulus_model.mimetype=mimetype
                session.commit()

                # Get or create Run Stimulus association
                runstim, _ = db_utils.get_or_create(session, RunStimulus,
                                                    commit=False,
                                                    stimulus_id=stimulus_model.id,
                                                    run_id=run_model.id)
                runstim.onset=onsets[i]
                session.commit()

    dataset_model.mimetypes = list(mimetypes)
    session.commit()

    """ Add GroupPredictors """
    # Participants
    participants_path = os.path.join(bids_path, 'participants.tsv')
    if os.path.exists(participants_path):
        if verbose:
            print("Processing participants.tsv")
        participants = pd.read_csv(participants_path, delimiter='\t')
        participants = dict(participants.iteritems())
        subs = participants.pop('participant_id')

        # Parse participant columns and insert as GroupPredictors
        for col in participants.keys():
            gp, _ = db_utils.get_or_create(session, GroupPredictor,
                                                  name=col,
                                                  dataset_id=dataset_model.id,
                                                  level='subject')

            for i, val in participants[col].items():
                sub_id = subs[i].split('-')[1]
                subject_runs = Run.query.filter_by(dataset_id=dataset_model.id,
                                                   subject=sub_id)
                for run in subject_runs:
                    gpv, _ = db_utils.get_or_create(session, GroupPredictorValue,
                                                   commit=False,
                                                   gp_id=gp.id,
                                                   run_id = run_model.id,
                                                   level_id=sub_id)
                    gpv.value = str(val)
                    session.commit()


    return dataset_model.id

def extract_features(session, bids_path, task, graph_spec, verbose=True, **kwargs):
    # Try to add dataset, will skip if already in
    dataset_id = add_dataset(session, bids_path, task, verbose=True)

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

    ef_model_ids = []
    for res in results:
        """" Add new ExtractedFeature """
        extractor = res.extractor
        # Hash extractor name + feature name
        ef_hash = hash_str(str(extractor.__hash__()) + res.features[0])
        tr_attrs = [getattr(res, attr) for attr in extractor._log_attributes]
        ef_params = str(dict(
            zip(extractor._log_attributes, tr_attrs)))

        # Get or create feature
        ef_model, ef_new = db_utils.get_or_create(session,
                                             ExtractedFeature,
                                             commit=False,
                                             extractor_name=extractor.name,
                                             extractor_parameters=ef_params,
                                             feature_name=res.features[0])
        if ef_new:
            ef_model.sha1_hash=ef_hash
            session.commit()

        ef_model_ids.append(ef_model.id)

        """" Add ExtractedEvents """
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

    """" Create Predictors from Extracted Features """
    # For all instances for stimuli in this task's runs
    task_runstimuli = RunStimulus.query.join(
        Run).filter(Run.dataset_id == dataset_id and Run.task==task).all()
    for rs in task_runstimuli:
        # For every feature extracted
        for ef_id in ef_model_ids:
            ef = ExtractedFeature.query.filter_by(id = ef_id).one()
            # Get ExtractedEvents associated with stimulus
            ees = ef.extracted_events.filter_by(
                stimulus_id = rs.stimulus_id).all()

            onsets = [ee.onset + rs.onset if ee.onset else rs.onset
                      for ee in ees]
            durations = [ee.duration for ee in ees]
            values = [ee.value for ee in ees if ee.value]

            predictor_name = '{}.{}'.format(ef.extractor_name, ef.feature_name)
            add_predictor(session, predictor_name, dataset_id, rs.run_id,
                          onsets, durations, values, ef_id = ef_id)

    return ef_model_ids
