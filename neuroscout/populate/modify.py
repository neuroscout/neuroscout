""" Dataset modification
Tools to modify/delete datasets already in database.

TODO
 - Add tools to create new predictors from existing features
"""

from models import (Dataset, Task, Run, RunStimulus, Stimulus,
                    ExtractedFeature, ExtractedEvent)
from database import db
from .extract import create_predictors

def delete_task(dataset, task):
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

    db.session.delete(task_model)
    db.session.commit()


def extend_extracted_objects(dataset_name, **selectors):
    """ Creates PredictorEvents for newly ingest runs in a Dataset,
        for all ExtractedFeatures. Also links derived Stimuli with new Runs.
        Args:
            dataset_name (str) - dataset name
            selectors (dict) - dictionary of lists of attributes to filter Runs.
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
                ## Create new rs
                new_rs.append(
                    RunStimulus(stimulus_id=stim.id,
                                run_id=run.id,
                                onset=copy_rs.onset,
                                duration=copy_rs.duration)
                    )

    db.session.bulk_save_objects(new_rs)
    db.session.commit()

    run_ids = runs.with_entities('Run.id')
    ## Get ExtractedFeatures linked to these Runs by Stimuli
    efs = ExtractedFeature.query.filter_by(active=True).join(
        ExtractedEvent).join(Stimulus).join(
            RunStimulus).filter(RunStimulus.run_id.in_(run_ids)).all()

    create_predictors(efs, dataset_name, run_ids)
