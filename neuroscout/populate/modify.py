""" Dataset modification
Tools to modify/delete datasets already in database.

TODO
 - Add tools to create new predictors from existing features
"""

from models import Dataset, Task

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
