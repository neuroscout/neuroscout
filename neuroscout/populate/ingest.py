""" Dataset ingestion
Tools to populate database from BIDS datasets
"""
import json
import magic
from flask import current_app
from pathlib import Path

import pandas as pd
import nibabel as nib

from bids.layout import BIDSLayout
from bids.variables import load_variables
from datalad.api import install

from core import cache
from .utils import remote_resource_exists, hash_stim
from utils import get_or_create
from models import (Dataset, Task, Run, Predictor, PredictorEvent, PredictorRun,
                    Stimulus, RunStimulus, GroupPredictor, GroupPredictorValue)
from database import db
from progressbar import progressbar
from .annotate import PredictorSerializer

def add_predictor_collection(collection, dataset_id, run_id, TR=None, include=None):
    """ Add a RunNode to the database.
    Args:
        collection - BIDSVariableCollection to ingest
        dataset_id - Dataset model id
        run_id - Run model id
        source - source of collection. e.g "events", "recordings"
        TR - time repetiton of task
        include - list of predictors to include. all if None.
    """
    pe_objects = []
    for var in collection.variables.values():
        annotated = PredictorSerializer(TR=TR, include=include).load(var)
        if annotated is not None:
            pred_props, pes_props = annotated
            predictor, _ = get_or_create(
                Predictor,dataset_id=dataset_id, **pred_props)
            for pe in pes_props:
                pe_objects.append(PredictorEvent(
                               predictor_id=predictor.id, run_id=run_id, **pe))
            # Add PredictorRun
            pr, _ = get_or_create(
                PredictorRun, predictor_id=predictor.id, run_id=run_id)

    db.session.bulk_save_objects(pe_objects)
    db.session.commit()

def add_group_predictors(dataset_id, participants):
    """ Adds group predictors using participants.tsv
    Args:
        participants - path to participants tsv
        dataset_id - Dataset model id
        subjects - subject ids to processed
    Output:
        Ids of group predictors added
    """
    gp_ids = []
    try:
        from os.path import isfile
        assert isfile(participants.as_posix())
        participants = pd.read_csv(participants, delimiter='\t')
    except:
        return []

    participants = dict(participants.iteritems())
    subs = participants.pop('participant_id')

    # Parse participant columns and insert as GroupPredictors
    for col in participants.keys():
        gp, _ = get_or_create(
            GroupPredictor, name=col, dataset_id=dataset_id, level='subject')

        for i, val in participants[col].items():
            sub_id = subs[i].split('-')[1]
            subject_runs = Run.query.filter_by(dataset_id=dataset_id,
                                               subject=sub_id)
            for run in subject_runs:
                gpv, _ = get_or_create(
                    GroupPredictorValue, commit=False,
                    gp_id=gp.id, run_id = run.id, level_id=sub_id)
                gpv.value = str(val)
        db.session.commit()
        gp_ids.append(gp.id)

    return gp_ids


def add_stimulus(stim_hash, dataset_id, parent_id=None, path=None, content=None,
                 converter_name=None, converter_params=None):
    """ Create stimulus model """
    if path is None and content is None:
        raise ValueError("Stimulus path and data cannot both be None")
    if path is not None:
        path = path.resolve().as_posix()
        mimetype = magic.from_file(path, mime=True)
    elif content is not None:
        mimetype = 'text/plain'

    model, new = get_or_create(
        Stimulus, commit=False, sha1_hash=stim_hash, parent_id=parent_id,
        dataset_id=dataset_id, converter_name=converter_name)

    if new:
        model.path = path
        model.content = content
        model.mimetype = mimetype
        model.converter_params = converter_params
        db.session.commit()

    return model, new


def add_task(task_name, dataset_name=None, local_path=None,
             dataset_address=None, preproc_address=None, include_predictors=None,
             reingest=False, scan_length=1000, dataset_summary=None,
             external=None, task_summary=None, **kwargs):
    """ Adds a BIDS dataset task to the database.
        Args:
            task_name - task to add
            dataset_name - overide dataset name
            local_path - path to local bids dataset.
            dataset_address - remote address of BIDS dataset.
            preproc_address - remote address of preprocessed files.
            include_predictors - set of predictors to ingest
            reingest - force reingesting even if dataset already exists
            scan_length - default scan length in case it cant be found in image
            dataset_summary - Dataset summary description,
            external - Dataset external link,
            task_summary - Task summary description,
            kwargs - arguments to filter runs by
        Output:
            dataset model id
    """
    cache.clear()

    if dataset_address is not None and local_path is None:
        local_path = install(
            source=dataset_address,
            path=(Path(
                current_app.config['DATASET_DIR']) / dataset_name).as_posix()
            ).path

    local_path = Path(local_path)

    from os.path import isfile
    assert isfile((local_path / 'dataset_description.json').as_posix())

    paths = [(local_path.as_posix(), 'bids')]
    if (local_path / 'derivatives').exists():
        paths.append(((local_path / 'derivatives').as_posix(), 'derivatives'))
    layout = BIDSLayout(paths, root=local_path.as_posix())

    if task_name not in layout.get_tasks():
        raise ValueError("Task {} not found in dataset {}".format(
            task_name, local_path))

    dataset_name = dataset_name if dataset_name is not None \
                   else layout.description['Name']

    # Get or create dataset model from mandatory arguments
    dataset_model, new_ds = get_or_create(Dataset, name=dataset_name)

    if new_ds:
        dataset_model.description = layout.description
        dataset_model.summary = dataset_summary,
        dataset_model.external = external,
        dataset_model.dataset_address = dataset_address
        dataset_model.preproc_address = preproc_address
        dataset_model.local_path = local_path.as_posix()
        db.session.commit()
    elif not reingest:
        return dataset_model.id

    # Get or create task
    task_model, new_task = get_or_create(
        Task, name=task_name, dataset_id=dataset_model.id)

    if new_task:
        task_model.description = json.load(
            (local_path / 'task-{}_bold.json'.format(task_name)).open())
        task_model.summary = task_summary,
        task_model.TR = task_model.description['RepetitionTime']
        db.session.commit()

    stims_processed = {}
    """ Parse every Run """
    current_app.logger.info("Parsing runs")
    all_runs = layout.get(task=task_name, suffix='bold', extensions='.nii.gz',
                          **kwargs)
    for img in progressbar(all_runs):
        """ Extract Run information """
        # Get entities
        entities = {entity : getattr(img, entity)
                    for entity in ['subject', 'session', 'acquisition']
                    if entity in img._fields}
        run_number = img.run if hasattr(img, 'run') else None

        run_model, new = get_or_create(
            Run, dataset_id=dataset_model.id, number=run_number,
            task_id = task_model.id, **entities)
        entities['task'] = task_model.name
        if run_number:
            entities['run'] = run_number

        # Get duration (helps w/ transformations)
        try:
            img_ni = nib.load(img.filename)
            run_model.duration = img_ni.shape[3] * img_ni.header.get_zooms()[-1]
        except (nib.filebasedimages.ImageFileError, IndexError) as e:
            current_app.logger.debug(
                "Error loading BOLD file, default duration used.")
            run_model.duration = scan_length

        path_patterns = ['sub-{subject}[ses-{session}/]/func/sub-{subject}_'
                         '[ses-{session}_]task-{task}_[acquisition-{acquisition}_]'
                         '[run-{run}_]bold_[space-{space}_]{suffix}.nii.gz']

        if 'run' in 'entities':
            entities['run'] = entities['run'].zfill(2)

        run_model.func_path = layout.build_path(
            {'suffix': 'preproc', 'space': 'MNI152NLin2009cAsym', **entities},
            path_patterns=path_patterns)
        run_model.mask_path = layout.build_path(
            {'suffix': 'brainmask', 'space': 'MNI152NLin2009cAsym', **entities},
            path_patterns=path_patterns)

        # Confirm remote address exists:
        if preproc_address is not None:
            remote_resource_exists(preproc_address, run_model.func_path)
            remote_resource_exists(preproc_address, run_model.mask_path)

        """ Extract Predictors"""
        # Assert event files exist (for DataLad)
        for e in layout._get_nearest_helper(img.filename, '.tsv', suffix='events'):
            assert isfile(e)

        collection = load_variables(
            layout, levels='run', scan_length=run_model.duration, **entities).\
        get_collections('run')[0]

        stims = collection.variables.pop('stim_file')

        add_predictor_collection(
            collection, dataset_model.id, run_model.id,
            include=include_predictors, TR=task_model.TR)

        """ Ingest Stimuli """
        for i, val in enumerate(stims.values):
            stim_path = local_path / 'stimuli' / val
            if val not in stims_processed:
                try:
                    stim_hash = hash_stim(stim_path)
                except OSError:
                    current_app.logger.debug('{} not found.'.format(stim_path))
                    continue

                stims_processed[val] = stim_hash
            else:
                stim_hash = stims_processed[val]

            stim_model, _ = add_stimulus(
                stim_hash, path=stim_path, dataset_id=dataset_model.id)

            # Get or create Run Stimulus association
            runstim, _ = get_or_create(
                RunStimulus, stimulus_id=stim_model.id, run_id=run_model.id,
                onset=stims.onset.tolist()[i],
                duration=stims.duration.tolist()[i])


    """ Add GroupPredictors """
    current_app.logger.info("Adding group predictors")
    add_group_predictors(dataset_model.id, local_path / 'participants.tsv')

    return dataset_model.id
