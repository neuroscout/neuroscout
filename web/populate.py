""" Functions to populate database from datasets and extracted features """
import os
import re
import json
import pandas as pd
from pathlib import Path

import db_utils
from utils import hash_file, hash_str

from bids.grabbids import BIDSLayout
from bids.transform import BIDSEventCollection

from models import (Dataset, Run, Predictor, PredictorEvent, PredictorRun,
                    Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent,
                    GroupPredictor, GroupPredictorValue, Task)

import magic
import nibabel as nib

def add_predictor(db_session, predictor_name, dataset_id, run_id,
                  onsets, durations, values, **kwargs):
    """" Adds a new Predictor to a run given a set of values
    If Predictor already exist, use that one
    Args:
        db_session - sqlalchemy db db_session
        predictor_name - name given to predictor_name
        dataset_id - dataset db id
        run_id - run db id
        onsets - list of onsets
        durations - list of durations
        values - list of values
        kwargs - additional identifiers of the Predictor
    Output:
        predictor id

    """
    predictor, _ = db_utils.get_or_create(db_session, Predictor,
                                          name=predictor_name,
                                          dataset_id=dataset_id,
                                          **kwargs)

    # Insert each row of Predictor as PredictorEvent
    for i, val in enumerate(values):
        pe, _ = db_utils.get_or_create(db_session, PredictorEvent,
                                       commit=False,
                                       onset=onsets[i],
                                       predictor_id=predictor.id,
                                       run_id = run_id)
        pe.duration = durations[i]
        pe.value = str(val)
        db_session.commit()

    # Add PredictorRun
    pr, _ = db_utils.get_or_create(db_session, PredictorRun,
                                   predictor_id=predictor.id,
                                   run_id = run_id)

    return predictor.id

def add_dataset(db_session, bids_path, task, replace=False, verbose=True,
                install_path='.', automagic=False, **kwargs):
    """ Adds a BIDS dataset task to the database.
        Args:
            db_session - sqlalchemy db db_session
            bids_path - path to local or remote bids directory.
                        remote paths must begin with "///" or be github link.
            task - task to add
            replace - if dataset/task already exists, skip or replace?
            verbose - verbose output
            install_path - if remote dataset, where to install.
                           current directory if none.
            kwargs - arguments to filter runs by
            automagic - enable automagic?
        Output:
            dataset model id
     """

    if re.match('(///|git+|http)', bids_path) and \
            open.__module__ != 'datalad.auto':
        from datalad import api as dl
        bids_path = dl.install(source=bids_path,
                               path=install_path).path
        automagic = True

    if automagic:
        from datalad.auto import AutomagicIO
        automagic = AutomagicIO()
        automagic.activate()

    layout = BIDSLayout(bids_path)
    if task not in layout.get_tasks():
        raise ValueError("No such task exists in BIDS dataset.")

    # Extract BIDS dataset info and store in dictionary
    description = json.load(open(
        os.path.join(bids_path, 'dataset_description.json'), 'r'))
    description['URL'] = ''
    task_description = json.load(open(
        os.path.join(bids_path, 'task-{}_bold.json'.format(task)), 'r'))

    dataset_name = description['Name']

    # Get or create dataset model from mandatory arguments
    dataset_model, new_ds = db_utils.get_or_create(db_session, Dataset,
                                                name=dataset_name)

    if new_ds:
        dataset_model.description = description
        db_session.commit()

    # Get or create task
    task_model, new_task = db_utils.get_or_create(db_session, Task,
                                                name=task,
                                                dataset_id=dataset_model.id,
                                                description=task_description)
    if new_task:
        task_model.description = task_description
        db_session.commit()
    else:
        if not replace:
            if automagic:
                automagic.deactivate()
            return dataset_model.id

    """ Parse every Run """
    for run_events in layout.get(task=task, type='events', **kwargs):
        if verbose:
            print("Processing task {} subject {}, run {}".format(
                run_events.task, run_events.subject, run_events.run))

        # Get entities
        entities = {entity : getattr(run_events, entity)
                    for entity in ['db_session', 'subject']
                    if entity in run_events._fields}

        """ Extract Run information """
        run_model, new = db_utils.get_or_create(db_session, Run,
                                                dataset_id=dataset_model.id,
                                                number=run_events.run,
                                                task_id = task_model.id,
                                                **entities)
        entities['run'] = run_events.run
        entities['task'] = task_model.name

        # Get BOLD
        try:
            img = nib.load(layout.get(type='bold', extensions='.nii.gz',
                              return_type='file', **entities)[0])
            run_model.duration = img.shape[3] * img.header.get_zooms()[-1] / 1000
        except (nib.filebasedimages.ImageFileError, IndexError) as e:
            print("Error loading BOLD file, duration not loaded.")

        preprocs = layout.get(type='preproc', return_type='file', **entities)

        try: # Try to get path of preprocessed data
            mni = [re.findall('derivatives.*MNI152.*', pre)
                       for pre in preprocs
                       if re.findall('derivatives.*MNI152.*', pre)]
            run_model.path = [item for sublist in mni for item in sublist][0]
        except IndexError:
            pass
        db_session.commit()

        """ Extract Predictors"""
        # Read event file and extract information
        tsv = pd.read_csv(open(run_events.filename, 'r'), delimiter='\t')
        tsv = dict(tsv.iteritems())
        onsets = tsv.pop('onset').tolist()
        durations = tsv.pop('duration').tolist()
        stims = tsv.pop('stim_file')

        # Parse event columns and insert as Predictors
        for predictor in tsv.keys():
            add_predictor(db_session, predictor, dataset_model.id, run_model.id,
                          onsets, durations, tsv[predictor].tolist())

        """ Ingest Stimuli """
        print("Ingesting stimuli...")
        for i, val in stims[stims!="n/a"].items():
            base_path = 'stimuli/{}'.format(val)
            path = os.path.join(bids_path, base_path)
            name = os.path.basename(path)
            try:
                _ = open(path)
                stim_hash = hash_file(path)
                mimetype = magic.from_file(os.path.realpath(path), mime=True)
            except FileNotFoundError:
                if verbose:
                    print('Stimulus: {} not found. Skipping.'.format(val))
                continue

            # Get or create stimulus model
            stimulus_model, _ = db_utils.get_or_create(db_session, Stimulus,
                                                       commit=False,
                                                       sha1_hash=stim_hash)
            stimulus_model.name=name
            stimulus_model.path=base_path
            stimulus_model.mimetype=mimetype
            db_session.commit()

            # Get or create Run Stimulus association
            runstim, _ = db_utils.get_or_create(db_session, RunStimulus,
                                                commit=False,
                                                stimulus_id=stimulus_model.id,
                                                run_id=run_model.id)
            runstim.onset=onsets[i]
            db_session.commit()

    db_session.commit()

    """ Add GroupPredictors """
    # Participants
    participants_path = os.path.join(bids_path, 'participants.tsv')
    if os.path.exists(participants_path):
        if verbose:
            print("Processing participants.tsv")
        participants = pd.read_csv(open(participants_path, 'r'), delimiter='\t')
        participants = dict(participants.iteritems())
        subs = participants.pop('participant_id')

        # Parse participant columns and insert as GroupPredictors
        for col in participants.keys():
            gp, _ = db_utils.get_or_create(db_session, GroupPredictor,
                                                  name=col,
                                                  dataset_id=dataset_model.id,
                                                  level='subject')

            for i, val in participants[col].items():
                sub_id = subs[i].split('-')[1]
                subject_runs = Run.query.filter_by(dataset_id=dataset_model.id,
                                                   subject=sub_id)
                for run in subject_runs:
                    gpv, _ = db_utils.get_or_create(db_session, GroupPredictorValue,
                                                   commit=False,
                                                   gp_id=gp.id,
                                                   run_id = run_model.id,
                                                   level_id=sub_id)
                    gpv.value = str(val)
                    db_session.commit()

    if automagic:
        automagic.deactivate()

    return dataset_model.id

def extract_features(db_session, bids_path, task, graph_spec, verbose=True,
                     auto_io=False, datalad_unlock=False, **kwargs):
    """ Extract features using pliers for a dataset/task
        Args:
            db_session - db db_session
            bids_path - bids dataset directory
            task - task name
            graph_spec - pliers graph json spec location
            verbose - verbose output
            kwargs - additional identifiers for runs

        Output:
            list of db ids of extracted features
    """


    import imageio
    try:
        from pliers.stimuli import load_stims
        from pliers.graph import Graph
    except imageio.core.fetching.NeedDownloadError:
        imageio.plugins.ffmpeg.download()
        from pliers.stimuli import load_stims
        from pliers.graph import Graph

    # Try to add dataset, will skip if already in
    dataset_id = add_dataset(db_session, bids_path, task, **kwargs)

    # Load event files
    collection = BIDSEventCollection(bids_path)
    collection.read(task=task, **kwargs)

    # Filter to only get stim files
    stim_pattern = 'stim_file/(.*)'
    stim_paths = [os.path.join(bids_path, 'stimuli',
                          re.findall(stim_pattern, col)[0])
     for col in collection.columns
     if re.match(stim_pattern, col)]

    # Monkey-patched auto doesn't work, so get and unlock manually
    if datalad_unlock:
        from datalad import api as da
        da.get(stim_paths)
        da.unlock(stim_paths)

    # Get absolute path and load
    stims = load_stims([s for s in stim_paths])

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
        ef_model, ef_new = db_utils.get_or_create(db_session,
                                             ExtractedFeature,
                                             commit=False,
                                             extractor_name=extractor.name,
                                             extractor_parameters=ef_params,
                                             feature_name=res.features[0])
        if ef_new:
            ef_model.sha1_hash=ef_hash
            db_session.commit()

        ef_model_ids.append(ef_model.id)

        """" Add ExtractedEvents """
        # Get associated stimulus record
        stim_hash = hash_file(res.stim.filename)
        stimulus = db_session.query(Stimulus).filter_by(sha1_hash=stim_hash).one()

        if not stimulus:
            raise Exception("Stimulus not found in database, have you added"
                            "this dataset to the database?")

        # Set onset for event
        onset = None if pd.isnull(res.onsets) else res.onsets[0]
        # Get or create ExtractedEvent
        ee_model, ee_new = db_utils.get_or_create(db_session,
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

        db_session.commit()

    """" Create Predictors from Extracted Features """
    # For all instances for stimuli in this task's runs
    task_runstimuli = RunStimulus.query.join(
        Run).filter(Run.dataset_id == dataset_id and Run.task.name==task).all()
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
            add_predictor(db_session, predictor_name, dataset_id, rs.run_id,
                          onsets, durations, values, ef_id = ef_id)

    return ef_model_ids

import yaml
def config_from_yaml(db_session, config_file, dataset_dir):
    datasets = yaml.load(open(config_file, 'r'))

    base_path = os.path.dirname(os.path.realpath(config_file))

    dataset_ids = []
    for name, items in datasets.items():
    	for task, options in items['tasks'].items():
            if 'filters' in options:
            	filters = options['filters']
            else:
            	filters = {}
            new_path = str((Path(
            	dataset_dir) / name).absolute())
            dataset_ids.append(add_dataset(db_session, items['path'], task,
            					replace=False, verbose=True,
            					install_path=new_path,
            					**filters))

            datalad_unlock = bool(re.match('(///|git+|http)',  items['path']))

            for graph in options['features']:
            	extract_features(db_session, new_path, task,
            		os.path.join(base_path, graph), datalad_unlock=datalad_unlock, **filters)


    return dataset_ids
