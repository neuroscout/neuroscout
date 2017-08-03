""" Functions to populate database from datasets and extracted features """
import os
import re
import json
import pandas as pd
from pathlib import Path

import db_utils
from utils import hash_file, hash_str

from bids.grabbids import BIDSLayout
from bids.events import BIDSEventCollection

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
    if isinstance(values, str):
        values = pd.Series(values, dtype='object')
    # Insert each row of Predictor as PredictorEvent
    for i, val in enumerate(values[values!='n/a']):
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

def add_dataset(db_session, task, replace=False, verbose=True,
                install_path='.', automagic=False, skip_predictors=False,
                address=None, bids_path=None, name=None, **kwargs):
    """ Adds a BIDS dataset task to the database.
        Args:
            db_session - sqlalchemy db db_session
            bids_path - path to local or remote bids directory.
                        remote paths must begin with "///" or be github link.
            task - task to add
            replace - if dataset/task already exists, skip or replace?
            verbose - verbose output
            install_path - if remote dataset, where to install.
            kwargs - arguments to filter runs by
            automagic - force enable DataLad automagic
            skip_predictors - skip ingesting original predictors
        Output:
            dataset model id
     """

    if address is not None and bids_path is None:
        from datalad import api as dl
        bids_path = dl.install(source=address,
                               path=install_path).path
        automagic = True

    if automagic:
        from datalad.auto import AutomagicIO
        automagic = AutomagicIO()
        automagic.activate()

    layout = BIDSLayout(bids_path)
    if task not in layout.get_tasks():
        raise ValueError("Task {} not found in dataset {}".format(
            task, bids_path))

    # Extract BIDS dataset info and store in dictionary
    description = json.load(open(
        os.path.join(bids_path, 'dataset_description.json'), 'r'))
    description['URL'] = ''
    task_description = json.load(open(
        os.path.join(bids_path, 'task-{}_bold.json'.format(task)), 'r'))

    if name is not None:
        dataset_name = name
    else:
        dataset_name = description['Name']

    # Get or create dataset model from mandatory arguments
    dataset_model, new_ds = db_utils.get_or_create(db_session, Dataset,
                                                name=dataset_name)

    if new_ds:
        dataset_model.description = description
        dataset_model.address = address
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

    # List of stimuli already processed
    stims_processed = {}

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
        masks = layout.get(type='brainmask', return_type='file', **entities)
        try: # Try to get path of preprocessed data
            func = [re.findall('derivatives.*MNI152.*', pre)
                       for pre in preprocs
                       if re.findall('derivatives.*MNI152.*', pre)]

            mask = [re.findall('derivatives.*MNI152.*', pre)
                       for pre in masks
                       if re.findall('derivatives.*MNI152.*', pre)]

            run_model.func_path = [item for sublist in func for item in sublist][0]
            run_model.mask_path = [item for sublist in mask for item in sublist][0]
        except IndexError:
            pass

        db_session.commit()

        if verbose:
            print("Extracting predictors")
        """ Extract Predictors"""
        # Read event file and extract information
        tsv = pd.read_csv(open(run_events.filename, 'r'), delimiter='\t')
        tsv = dict(tsv.iteritems())
        onsets = tsv.pop('onset').tolist()
        durations = tsv.pop('duration').tolist()
        stims = tsv.pop('stim_file')

        if skip_predictors is False:
            # Parse event columns and insert as Predictors
            for predictor in tsv.keys():
                add_predictor(db_session, predictor, dataset_model.id, run_model.id,
                              onsets, durations, tsv[predictor])

        if verbose:
            print("Ingesting stimuli")
        """ Ingest Stimuli """
        for i, val in stims[stims!="n/a"].items():
            base_path = 'stimuli/{}'.format(val)
            path = os.path.join(bids_path, base_path)
            name = os.path.basename(path)

            # If stim has already been processed, skip adding it
            if val not in stims_processed:
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

                stims_processed[val] = stim_hash
            else:
                # Get or create stimulus model
                stimulus_model, _ = db_utils.get_or_create(db_session, Stimulus,
                                                           commit=False,
                                                           sha1_hash=stims_processed[val])

            db_session.commit()

            # Get or create Run Stimulus association
            runstim, _ = db_utils.get_or_create(db_session, RunStimulus,
                                                commit=False,
                                                stimulus_id=stimulus_model.id,
                                                run_id=run_model.id)
            runstim.onset=onsets[i]

    db_session.commit()

    if verbose:
        print("Adding group predictors")
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
                     automagic=False, **filters):
    """ Extract features using pliers for a dataset/task
        Args:
            db_session - db db_session
            bids_path - bids dataset directory
            task - task name
            graph_spec - pliers graph json spec location
            verbose - verbose output
            filters - additional identifiers for runs
            autoamgic - enable automagic and unlock stimuli with datalad
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
    dataset_id = add_dataset(db_session, task, bids_path=bids_path, **filters)


    # Load event files
    collection = BIDSEventCollection(bids_path)
    collection.read(task=task, **filters)

    # Filter to only get stim files
    stim_pattern = 'stim_file/(.*)'
    stim_paths = [os.path.join(bids_path, 'stimuli',
                          re.findall(stim_pattern, col)[0])
     for col in collection.columns
     if re.match(stim_pattern, col)]

    # Monkey-patched auto doesn't work, so get and unlock manually
    if automagic:
        from datalad import api as da
        da.get(stim_paths)
        da.unlock(stim_paths)

    # Get absolute path and load
    stims = load_stims([os.path.realpath(s) for s in stim_paths])


    # Construct and run the graph
    graph = Graph(spec=graph_spec)
    results = graph.run(stims, merge=False)

    extracted_features = {}
    for res in results:
        """" Add new ExtractedFeature """
        extractor = res.extractor
        # Hash extractor name + feature name
        ef_hash = hash_str(str(extractor.__hash__()) + res.features[0])

        # If we haven't already added this feature
        if ef_hash not in extracted_features:
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
            ef_model.sha1_hash=ef_hash
            db_session.commit()

            extracted_features[ef_hash] = ef_model.id

        """" Add ExtractedEvents """
        # Get associated stimulus record
        filename = res.stim.history.source_file \
                    if res.stim.history \
                    else res.stim.filename
        stim_hash = hash_file(filename)
        stimulus = db_session.query(Stimulus).filter_by(sha1_hash=stim_hash).one()

        # Set onset for event
        if pd.isnull(res.onsets):
            onset = None
        elif isinstance(res.onsets, float):
            onset = res.onsets
        else:
            onset = res.onsets[0]

        # Get or create ExtractedEvent
        ee_model, ee_new = db_utils.get_or_create(db_session,
                                               ExtractedEvent,
                                               commit=False,
                                               onset=onset,
                                               stimulus_id=stimulus.id,
                                               ef_id=extracted_features[ef_hash])

        # Add data to it (whether or not its new, as we may want to update)
        ee_model.value = res.data[0][0]
        if pd.isnull(res.durations):
            ee_model.duration = None
        elif isinstance(res.durations, float):
            ee_model.duration = res.durations
        else:
            ee_model.duration = res.durations[0]

        ee_model.history = res.history.string

        db_session.commit()

    """" Create Predictors from Extracted Features """
    # For all instances for stimuli in this task's runs
    task_runstimuli = RunStimulus.query.join(
        Run).filter(Run.dataset_id == dataset_id and Run.task.name==task).all()
    for rs in task_runstimuli:
        # For every feature extracted
        for ef, ef_id in extracted_features.items():
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

    return list(extracted_features.values())

import yaml
def ingest_from_yaml(db_session, config_file, install_path='/file-data', automagic=False,
                     replace=False):
    datasets = yaml.load(open(config_file, 'r'))

    base_path = os.path.dirname(os.path.realpath(config_file))

    # Add each dataset in config file to db
    dataset_ids = []
    for name, items in datasets.items():
        address = items.get('address')
        path = items.get('path')
        if not (path or address):
            raise Exception("Must provide path or remote address")

        # If dataset is remote link, set path where to install
        if path is None:
            new_path = str((Path(install_path) / name).absolute())
        else:
            new_path = items['path']

        for task, options in items['tasks'].items():
            filters = options.get('filters', {})

            dp = options.get('dataset_parameters', {})

            dataset_ids.append(add_dataset(db_session, task,
                                bids_path=path, address=address,
            					replace=replace, automagic=automagic,
                                verbose=True, install_path=new_path,
                                name=name,
            					**dict(filters.items() | dp.items())))

            ep = options.get('extract_parameters',{})

            # Extract features if pliers graphs are provided
            if 'features' in options:
                for graph in options['features']:
                	extract_features(db_session, new_path, task,
                		os.path.join(base_path, graph),
                        automagic=path is None or automagic,
                        **dict(filters.items() | ep.items()))


    return dataset_ids
