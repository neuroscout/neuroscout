""" Functions to populate database from datasets and extracted features """
import os
import re
import json
import yaml
import pandas as pd
from pathlib import Path

import db_utils
from utils import hash_file, hash_str, remote_resource_exists, format_preproc

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

def add_group_predictors(db_session, dataset_id, participants):
    """ Adds group predictors using participants.tsv
    Args:
        participants - path to participants tsv, or pandas file
        dataset_id - Dataset model id
        subjects - subject ids to processed
    Output:
        Ids of group predictors added
    """
    gp_ids = []
    if isinstance(participants, str):
        try:
            participants = pd.read_csv(open(participants, 'r'), delimiter='\t')
        except FileNotFoundError:
            return []

    participants = dict(participants.iteritems())
    subs = participants.pop('participant_id')

    # Parse participant columns and insert as GroupPredictors
    for col in participants.keys():
        gp, _ = db_utils.get_or_create(db_session, GroupPredictor,
                                              name=col,
                                              dataset_id=dataset_id,
                                              level='subject')

        for i, val in participants[col].items():
            sub_id = subs[i].split('-')[1]
            subject_runs = Run.query.filter_by(dataset_id=dataset_id,
                                               subject=sub_id)
            for run in subject_runs:
                gpv, _ = db_utils.get_or_create(db_session,
                                                GroupPredictorValue,
                                                commit=False,
                                                gp_id=gp.id,
                                                run_id = run.id,
                                                level_id=sub_id)
                gpv.value = str(val)
        db_session.commit()
        gp_ids.append(gp.id)

    return gp_ids

def add_task(db_session, task, name=None, local_path=None, dataset_address=None,
             preproc_address=None, install_path='.', automagic=False,
             replace=False, verbose=True, skip_predictors=False, **kwargs):
    """ Adds a BIDS dataset task to the database.
        Args:
            db_session - sqlalchemy db db_session
            task - task to add
            name - overide dataset name
            local_path - path to local bids dataset.
            dataset_address - remote address of BIDS dataset.
            preproc_address - remote address of preprocessed files.
            install_path - if remote with no local path, where to install.
            automagic - force enable DataLad automagic
            replace - if dataset/task already exists, skip or replace?
            verbose - verbose output
            skip_predictors - skip ingesting original predictors
            kwargs - arguments to filter runs by
        Output:
            dataset model id
     """

    if dataset_address is not None and local_path is None:
        from datalad import api as dl
        local_path = dl.install(source=dataset_address,
                               path=install_path).path
        automagic = True

    if automagic:
        from datalad.auto import AutomagicIO
        automagic = AutomagicIO()
        automagic.activate()

    layout = BIDSLayout(local_path)
    if task not in layout.get_tasks():
        raise ValueError("Task {} not found in dataset {}".format(
            task, local_path))

    dataset_description = json.load(open(
        os.path.join(local_path, 'dataset_description.json'), 'r'))
    dataset_name = name if name is not None else dataset_description['Name']

    # Get or create dataset model from mandatory arguments
    dataset_model, new_ds = db_utils.get_or_create(
        db_session, Dataset, name=dataset_name)

    if new_ds or replace:
        dataset_model.description = dataset_description
        dataset_model.dataset_address = dataset_address
        dataset_model.preproc_address = preproc_address
        dataset_model.local_path = local_path
        db_session.commit()

    # Get or create task
    task_model, new_task = db_utils.get_or_create(
        db_session, Task, name=task, dataset_id=dataset_model.id)

    if new_task:
        task_model.description = json.load(open(
            os.path.join(local_path, 'task-{}_bold.json'.format(task)), 'r'))
        task_model.TR = task_model.description['RepetitionTime']
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
                    for entity in ['subject', 'session']
                    if entity in run_events._fields}

        """ Extract Run information """
        run_model, new = db_utils.get_or_create(db_session, Run,
                                                dataset_id=dataset_model.id,
                                                number=run_events.run,
                                                task_id = task_model.id,
                                                **entities)
        entities['run'] = run_events.run
        entities['task'] = task_model.name

        # Get duration (helps w/ transformations)
        try:
            img = nib.load(layout.get(type='bold', extensions='.nii.gz',
                              return_type='file', **entities)[0])
            run_model.duration = img.shape[3] * img.header.get_zooms()[-1] / 1000
        except (nib.filebasedimages.ImageFileError, IndexError) as e:
            print("Error loading BOLD file, duration not loaded.")

        run_model.func_path = format_preproc(suffix="preproc", **entities)
        run_model.mask_path = format_preproc(suffix="brainmask", **entities)
        db_session.commit()

        # Confirm remote address exists:
        if dataset_model.preproc_address is not None:
            remote_resource_exists(dataset_model.preproc_address, run_model.func_path)
            remote_resource_exists(dataset_model.preproc_address, run_model.mask_path)

        """ Extract Predictors"""
        if verbose:
            print("Extracting predictors")
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

        """ Ingest Stimuli """
        if verbose:
            print("Ingesting stimuli")

        stims_processed = {}
        for i, val in stims[stims!="n/a"].items():
            base_path = 'stimuli/{}'.format(val)
            path = os.path.join(local_path, base_path)
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
                stims_processed[val] = stim_hash
            else:
                stim_hash = stims_processed[val]

            # Get or create stimulus model
            stimulus_model, new_stim = db_utils.get_or_create(
                db_session, Stimulus, commit=False, sha1_hash=stim_hash)
            if new_stim:
                stimulus_model.name=name
                stimulus_model.path=local_path
                stimulus_model.mimetype=mimetype
            db_session.commit()

            # Get or create Run Stimulus association
            runstim, _ = db_utils.get_or_create(db_session, RunStimulus,
                                                commit=False,
                                                stimulus_id=stimulus_model.id,
                                                run_id=run_model.id)
            runstim.onset=onsets[i]
            runstim.duration=durations[i]
            db_session.commit()

    db_session.commit()

    """ Add GroupPredictors """
    if verbose:
        print("Adding group predictors")
    add_group_predictors(db_session, dataset_model.id,
                         os.path.join(local_path, 'participants.tsv'))

    if automagic:
        automagic.deactivate()

    return dataset_model.id

def extract_features(db_session, local_path, name, task, graph_spec,
                     automagic=False, verbose=True, **filters):
    """ Extract features using pliers for a dataset/task
        Args:
            db_session - db db_session
            local_path - bids dataset directory
            task - task name
            graph_spec - pliers graph json spec location
            verbose - verbose output
            filters - additional identifiers for runs
            automagic - enable automagic and unlock stimuli with datalad
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

    # ### CHANGE THIS TO LOOK UP ONLY. FAIL IF DS NOT FOUND
    dataset_id = add_task(db_session, task, local_path=local_path,
                             name=name, **filters)


    # Load event files
    collection = BIDSEventCollection(local_path)
    collection.read(task=task, **filters)

    # Filter to only get stim files
    stim_pattern = 'stim_file/(.*)'
    stim_paths = [os.path.join(local_path, 'stimuli',
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

            # If only a single value was extracted, and there is no duration
            # Set to stimulus duration
            if (len(durations) == 1) and (durations[0] is None):
                durations[0] = rs.duration

            values = [ee.value for ee in ees if ee.value]

            predictor_name = '{}.{}'.format(ef.extractor_name, ef.feature_name)
            add_predictor(db_session, predictor_name, dataset_id, rs.run_id,
                          onsets, durations, values, ef_id = ef_id)

    return list(extracted_features.values())

def ingest_from_yaml(db_session, config_file, install_path='/file-data',
                     automagic=False, replace=False):
    dataset_config = yaml.load(open(config_file, 'r'))
    config_path = os.path.dirname(os.path.realpath(config_file))

    """ Loop over each dataset in config file """
    dataset_ids = []
    for name, items in dataset_config.items():
        dataset_address = items.get('dataset_address')
        preproc_address = items.get('preproc_address')
        local_path = items.get('path')
        if not (local_path or dataset_address):
            raise Exception("Must provide path or remote address to dataset.")

        # If dataset is remote link, set install path
        if local_path is None:
            new_path = str((Path(install_path) / name).absolute())
        else:
            new_path = local_path

        for task, options in items['tasks'].items():
            # Add each task to database
            filters = options.get('filters', {})
            dp = options.get('dataset_parameters', {})

            dataset_id = add_task(db_session, task,
                                  local_path=local_path,
                                  dataset_address=dataset_address,
                                  replace=replace, automagic=automagic,
                                  verbose=True, install_path=new_path,
                                  preproc_address=preproc_address,
                                  name=name,
            					  **dict(filters.items() | dp.items()))
            dataset_ids.append(dataset_id)

            # Extract features if pliers graphs are provided
            ep = options.get('extract_parameters',{})

            if 'features' in options:
                for graph_spec in options['features']:
                	extract_features(db_session, new_path, name, task,
                		os.path.join(config_path, graph_spec),
                        automagic=local_path is None or automagic,
                        **dict(filters.items() | ep.items()))

    return dataset_ids

def delete_task(db_session, dataset, task):
    """ Deletes BIDS dataset task from the database, and *all* associated
    data in other tables.
        Args:
            db_session - sqlalchemy db db_session
            dataset - name of dataset
            task - name of task
    """
    dataset_model = Dataset.query.filter_by(name=dataset).one_or_none()
    if not dataset_model:
        raise ValueError("Dataset not found, cannot delete task.")

    task_model = Task.query.filter_by(name=task,
                                         dataset_id=dataset_model.id).one_or_none()
    if not task_model:
        raise ValueError("Task not found, cannot delete.")

    db_session.delete(task_model)
    db_session.commit()
