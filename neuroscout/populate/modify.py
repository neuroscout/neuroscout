""" Dataset modification
Tools to modify/delete datasets already in database.
"""

import json
import re
from flask import current_app
from ..models import (Dataset, Task, Run, RunStimulus, Stimulus,
                      ExtractedFeature, ExtractedEvent, Predictor)
from ..database import db
from .extract import create_predictors


def delete_task(dataset, task):
    """ Deletes BIDS dataset task from the database, and *all* associated
    data in other tables.
        Args:
            dataset - name of dataset
            task - name of task
    """
    dataset_model = Dataset.query.filter_by(name=dataset).one_or_none()
    if not dataset_model:
        raise ValueError("Dataset not found, cannot delete task.")

    task_model = Task.query.filter_by(
        name=task, dataset_id=dataset_model.id).one_or_none()
    if not task_model:
        raise ValueError("Task not found, cannot delete.")

    db.session.delete(task_model)
    db.session.commit()


def extend_extracted_objects(dataset_name, **selectors):
    """ Links RunStimuli for newly ingest runs in a Dataset,
        for all ExtractedFeatures. Also links derived Stimuli with new Runs.
        Args:
            dataset_name (str) - dataset name
            selectors (dict) - dict of lists of attributes to filter Runs.
    """
    # Filter runs
    run_ids = Run.query
    for key, value in selectors.items():
        run_ids = run_ids.filter(getattr(Run, key).in_(value))
    runs = run_ids.join(Dataset).filter_by(
        name=dataset_name)

    # Create RunStimulus associations with derived stimuli
    new_rs = []
    for run in runs:
        for rs in RunStimulus.query.filter_by(run_id=run.id):
            for stim in Stimulus.query.filter_by(parent_id=rs.stimulus_id):
                copy_rs = stim.run_stimuli.join(Run).filter_by(
                    number=run.number, session=run.session).first()
                # Create new rs
                new_rs.append(
                    RunStimulus(stimulus_id=stim.id,
                                run_id=run.id,
                                onset=copy_rs.onset,
                                duration=copy_rs.duration)
                    )

    db.session.bulk_save_objects(new_rs)
    db.session.commit()

    run_ids = runs.with_entities('Run.id')
    # Get ExtractedFeatures linked to these Runs by Stimuli
    efs = ExtractedFeature.query.filter_by(active=True).join(
        ExtractedEvent).join(Stimulus).join(
            RunStimulus).filter(RunStimulus.run_id.in_(run_ids)).all()

    create_predictors(efs, dataset_name, run_ids)


def update_annotations(mode='predictors', **kwargs):
    """ Update existing annotation in accordance with schema.
    Args:
        mode - Update 'predictors', 'features'
        kwargs - Additional filters on queries
    """
    if mode == 'predictors':
        schema = json.load(open(current_app.config['PREDICTOR_SCHEMA']))
        for pattern, atr in schema.items():
            matching = Predictor.query.filter(
                Predictor.original_name.op("~")(pattern)).filter_by(
                    ef_id=None, **kwargs)

            for match in matching:
                match.name = re.sub(
                    pattern, atr['name'], match.original_name) \
                    if 'name' in atr else match.name
                match.description = re.sub(
                    pattern, atr['description'], match.original_name) \
                    if 'description' in atr else None
                if atr.get('source') is not None:
                    match.source = atr['source']
            db.session.commit()

    elif mode == 'features':
        schema = json.load(open(current_app.config['FEATURE_SCHEMA']))
        ext_name = kwargs.pop('extractor_name') \
            if 'extractor_name' in kwargs else None
        for extractor_name, args in schema.items():
            if ext_name is not None and ext_name != extractor_name:
                continue
            candidate_efs = ExtractedFeature.query.filter_by(
                extractor_name=extractor_name, **kwargs)

            # Warning, does not check against Extractor Parameters
            for version in args:
                for pattern, atr in version['features'].items():
                    matching = candidate_efs.filter(
                        ExtractedFeature.original_name.op("~")(pattern))
                    for match in matching:
                        match.feature_name = re.sub(
                            pattern, atr['name'], match.original_name) \
                            if 'name' in atr else match.feature_name
                        match.description = re.sub(
                            pattern, atr['description'], match.original_name) \
                            if 'description' in atr else None
                        for pred in match.generated_predictors:
                            pred.name = match.feature_name
                            pred.description = match.description
                    db.session.commit()
