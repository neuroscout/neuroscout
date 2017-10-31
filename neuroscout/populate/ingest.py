""" Dataset ingestion
Tools to populate database from BIDS datasets
"""

from os.path import dirname, realpath, join, basename
import json
from pathlib import Path
import magic

import pandas as pd
import nibabel as nib

from bids.grabbids import BIDSLayout
from datalad import api as dl
from datalad.auto import AutomagicIO

import db_utils
from .utils import hash_file, remote_resource_exists, format_preproc
from models import (Dataset, Task, Run, Predictor, PredictorEvent, PredictorRun,
                    Stimulus, RunStimulus, GroupPredictor, GroupPredictorValue)

import populate

def ingest_from_json(db_session, config_file, install_path='/file-data',
                     automagic=False):
    dataset_config = json.load(open(config_file, 'r'))
    config_path = dirname(realpath(config_file))

    """ Loop over each dataset in config file """
    dataset_ids = []
    for dataset_name, items in dataset_config.items():
        dataset_address = items.get('dataset_address')
        preproc_address = items.get('preproc_address')
        local_path = items.get('path')
        if not (local_path or dataset_address):
            raise Exception("Must provide path or remote address to dataset.")

        # If dataset is remote link, set install path
        if local_path is None:
            new_path = str((Path(install_path) / dataset_name).absolute())
        else:
            new_path = local_path

        for task_name, options in items['tasks'].items():
            # Add each task to database
            filters = options.get('filters', {})
            dp = options.get('dataset_parameters', {})

            dataset_id = add_task(db_session, task_name,
                                  dataset_name=dataset_name,
                                  local_path=local_path,
                                  dataset_address=dataset_address,
                                  automagic=automagic,
                                  verbose=True, install_path=new_path,
                                  preproc_address=preproc_address,
            					  **dict(filters.items() | dp.items()))
            dataset_ids.append(dataset_id)

            # Extract features if pliers graphs are provided
            ep = options.get('extract_parameters',{})

            if 'features' in options:
                for graph_spec in options['features']:
                	populate.extract_features(db_session, dataset_name, task_name,
                		join(config_path, graph_spec),
                        automagic=local_path is None or automagic,
                        **dict(filters.items() | ep.items()))

    return dataset_ids

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

def add_task(db_session, task_name, dataset_name=None, local_path=None, dataset_address=None,
             preproc_address=None, install_path='.', automagic=False,
             verbose=True, skip_predictors=False, **kwargs):
    """ Adds a BIDS dataset task to the database.
        Args:
            db_session - sqlalchemy db db_session
            task_name - task to add
            dataset_namename - overide dataset name
            local_path - path to local bids dataset.
            dataset_address - remote address of BIDS dataset.
            preproc_address - remote address of preprocessed files.
            install_path - if remote with no local path, where to install.
            automagic - force enable DataLad automagic
            verbose - verbose output
            skip_predictors - skip ingesting original predictors
            kwargs - arguments to filter runs by
        Output:
            dataset model id
     """

    if dataset_address is not None and local_path is None:
        local_path = dl.install(source=dataset_address,
                               path=install_path).path
        automagic = True

    if automagic:
        automagic = AutomagicIO()
        automagic.activate()

    layout = BIDSLayout(local_path)
    if task_name not in layout.get_tasks():
        raise ValueError("Task {} not found in dataset {}".format(
            task_name, local_path))

    dataset_description = json.load(open(
        join(local_path, 'dataset_description.json'), 'r'))
    dataset_name = dataset_name if dataset_name is not None else dataset_description['Name']

    # Get or create dataset model from mandatory arguments
    dataset_model, new_ds = db_utils.get_or_create(
        db_session, Dataset, name=dataset_name)

    if new_ds:
        dataset_model.description = dataset_description
        dataset_model.dataset_address = dataset_address
        dataset_model.preproc_address = preproc_address
        dataset_model.local_path = local_path
        db_session.commit()
    else:
        if automagic:
            automagic.deactivate()
        return dataset_model.id

    # Get or create task
    task_model, new_task = db_utils.get_or_create(
        db_session, Task, name=task_name, dataset_id=dataset_model.id)

    if new_task:
        task_model.description = json.load(open(
            join(local_path, 'task-{}_bold.json'.format(task_name)), 'r'))
        task_model.TR = task_model.description['RepetitionTime']
        db_session.commit()


    """ Parse every Run """
    for run_events in layout.get(task=task_name, type='events', **kwargs):
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
            path = join(local_path, base_path)
            name = basename(path)

            # If stim has already been processed, skip adding it
            if val not in stims_processed:
                try:
                    _ = open(path)
                    stim_hash = hash_file(path)
                    mimetype = magic.from_file(realpath(path), mime=True)
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
                         join(local_path, 'participants.tsv'))

    if automagic:
        automagic.deactivate()

    return dataset_model.id
