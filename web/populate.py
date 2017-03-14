""" Populate database from command line """
import os

from flask_script import Manager
from app import app
from database import db
import json

from bids.grabbids import BIDSLayout

app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)
manager = Manager(app)

@manager.command
def add_dataset(bids_path, task):
    dataset_di = {}
    dataset_di['description'] = json.load(open(
        os.path.join(bids_path, 'dataset_description.json'), 'r'))
    dataset_di['task_description'] = json.load(open(
        os.path.join(bids_path, 'task-{}_bold.json'.format(task)), 'r'))
    dataset_di['name'] = dataset_di['description']['Name']
    dataset_di['task'] = task

    layout = BIDSLayout(bids_path)

    if task not in layout.get_tasks():
        raise ValueError("No such task")

    from models import Dataset
    dataset = Dataset.query.filter_by(name=dataset_di['name']).first()
    if dataset:
        print("Dataset already in db.")
    else:
        dataset = Dataset(**dataset_di)
        db.session.add(dataset)
        db.session.commit()

    from models import Run
    for run in layout.get(task=task, type='events'):
        run_model = Run(subject=run.subject, number=run.run, task=task,
                        dataset_id=dataset.id)
        db.session.add(run_model)
        db.session.commit()


if __name__ == '__main__':
    manager.run()
