""" Dataset ingestion
Tools to populate database from BIDS datasets
"""
import json
import magic
from os.path import isfile
from flask import current_app
from pathlib import Path

import pandas as pd

from bids.layout import BIDSLayout

from ..core import cache
from .utils import hash_stim
from ..utils.db import get_or_create
from ..models import (
    Dataset, Task, Run, Predictor, PredictorEvent, PredictorRun, Stimulus,
    RunStimulus, GroupPredictor, GroupPredictorValue)
from ..database import db
from tqdm import tqdm
from .annotate import PredictorSerializer


def add_predictor_collection(collection, dataset_id, run_id,
                             TR=None, include=None, exclude=None):
    """ Add a RunNode to the database.
    Args:
        collection - BIDSVariableCollection to ingest
        dataset_id - Dataset model id
        run_id - Run model id
        TR - time repetiton of task
        include - list of predictors to include. all if None.
    """
    pe_objects = []
    for var in collection.variables.values():
        annotated = PredictorSerializer(
            TR=TR, include=include, exclude=exclude).load(var)
        if annotated is not None:
            pred_props, pes_props = annotated
            predictor, _ = get_or_create(
                Predictor, dataset_id=dataset_id, **pred_props)
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
                    gp_id=gp.id, run_id=run.id, level_id=sub_id)
                gpv.value = str(val)
        db.session.commit()
        gp_ids.append(gp.id)

    return gp_ids


def add_stimulus(stim_hash, dataset_id, parent_id=None, path=None,
                 content=None, converter_name=None, converter_params=None,
                 mimetype=None):
    """ Create stimulus model """
    if mimetype is None:
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


def add_dataset(dataset_name, dataset_summary, preproc_address, local_path,
                dataset_address=None, dataset_long_description=None, url=None,
                reingest=False):
    cache.clear()

    local_path = Path(local_path)

    with (local_path / 'dataset_description.json').open() as f:
        description = json.load(f)

    # Get or create dataset model from name
    dataset_model, new_ds = get_or_create(Dataset, name=dataset_name)

    if new_ds or reingest:
        print(f"Adding dataset {dataset_name}")
        dataset_model.description = description
        dataset_model.summary = dataset_summary,
        dataset_model.long_description = dataset_long_description,
        dataset_model.url = url,
        dataset_model.dataset_address = dataset_address
        dataset_model.preproc_address = preproc_address
        dataset_model.local_path = local_path.as_posix()
        db.session.commit()
    else:
        print("Dataset found, skipping ingestion...")
        return dataset_model.id

    """ Add GroupPredictors """
    print("Adding group predictors")
    add_group_predictors(dataset_model.id, local_path / 'participants.tsv')

    return dataset_model.id


def add_task(task_name, dataset_name, local_path,
             include_predictors=None, exclude_predictors=None,
             reingest=False, scan_length=1000,
             summary=None, layout=None, **kwargs):
    """ Adds a BIDS dataset task to the database.
        Args:
            task_name - task to add
            dataset_name - dataset name
            local_path - path to local bids dataset.
            include_predictors - set of predictors to ingest
            exclude_predictors - set of predictors to exclude from ingestions
            reingest - force reingesting even if dataset already exists
            scan_length - default scan length in case it cant be found in image
            summary - Task summary description,
            layout - Preinstantiated BIDSLayout
            kwargs - arguments to filter runs by
        Output:
            dataset model id
    """
    cache.clear()
    print(f"Adding task {task_name}")

    if not layout:
        layout = BIDSLayout(
            str(local_path), derivatives=True, 
            suffix='bold', extension='nii.gz'
            )

    if task_name not in layout.get_tasks():
        raise ValueError("Task {} not found in dataset {}".format(
            task_name, local_path))

    # Get dataset model from name
    dataset_model = Dataset.query.filter_by(name=dataset_name)
    if dataset_model.count() != 1:
        raise Exception("Dataset not found")
    else:
        dataset_model = dataset_model.one()

    # Get or create task
    task_model, new_task = get_or_create(
        Task, name=task_name, dataset_id=dataset_model.id)

    local_path = Path(local_path)

    all_runs = layout.get(
        task=task_name, suffix='bold', extension='nii.gz',
        scope='raw', **kwargs)

    if new_task or reingest:
        # Pull first run's metadata as representative
        task_metadata = all_runs[0].get_metadata()
        task_model.description = task_metadata
        task_model.summary = summary,
        task_model.TR = task_metadata['RepetitionTime']
        db.session.commit()
    else:
        print("Task found, skipping ingestion...")
        return task_model.id

    stims_processed = {}
    """ Parse every Run """
    print("Parsing runs")
    for img in tqdm(all_runs):
        """ Extract Run information """
        # Get entities
        entities = {entity: getattr(img, entity)
                    for entity in ['subject', 'session', 'acquisition']
                    if entity in img.entities}
        run_number = img.run if hasattr(img, 'run') else None

        run_model, new = get_or_create(
            Run, dataset_id=dataset_model.id, number=run_number,
            task_id=task_model.id, **entities)
        entities['task'] = task_model.name
        if run_number:
            run_number = str(run_number).zfill(2)
            entities['run'] = run_number

        # Get duration (helps w/ transformations)
        try:
            niimg = img.get_image()
            run_model.duration = niimg.shape[3] * niimg.header.get_zooms()[-1]
        except ValueError:
            run_model.duration = scan_length

        # Put back as int
        if 'run' in entities:
            entities['run'] = int(entities['run'])

        """ Extract Predictors"""
        # Assert event files exist (for DataLad)
        for e in layout.get_nearest(
          img.path, suffix='events', all_=True, strict=False):
            assert isfile(e)

        collection = layout.get_collections(
            'run', scan_length=run_model.duration, desc=None,
            **entities)[0]

        if 'stim_file' in collection.variables:
            stims = collection.variables.pop('stim_file')
        else:
            stims = None

        add_predictor_collection(
            collection, dataset_model.id, run_model.id,
            include=include_predictors,
            exclude=exclude_predictors, TR=task_model.TR)

        """ Ingest Stimuli """
        if stims is not None:
            for i, val in enumerate(stims.values):
                stim_path = local_path / 'stimuli' / val
                if val not in stims_processed:
                    try:
                        stim_hash = hash_stim(stim_path)
                    except OSError:
                        current_app.logger.debug(
                            '{} not found.'.format(stim_path))
                        continue

                    stims_processed[val] = stim_hash
                else:
                    stim_hash = stims_processed[val]
                stim_model, _ = add_stimulus(
                    stim_hash, path=stim_path, dataset_id=dataset_model.id)

                # Get or create Run Stimulus association
                runstim, _ = get_or_create(
                    RunStimulus, stimulus_id=stim_model.id,
                    run_id=run_model.id,
                    onset=stims.onset.tolist()[i])
                runstim.duration = stims.duration.tolist()[i]
                db.session.commit()

    return task_model.id