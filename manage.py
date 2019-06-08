"""
    Command line management tools.
"""
import os
import requests
import json
import datetime

from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_security.utils import encrypt_password

from neuroscout import populate
from neuroscout.core import app, db
from neuroscout.models import user_datastore

app.config.from_object(os.environ['APP_SETTINGS'])
migrate = Migrate(app, db, directory=app.config['MIGRATIONS_DIR'])
manager = Manager(app)


def _make_context():
    from neuroscout import models
    from neuroscout.tests.request_utils import Client
    from neuroscout import resources

    try:
        client = Client(requests, 'http://127.0.0.1:80',
                        username='test2@test.com', password='password')
    except:
        client = None

    return dict(app=app, db=db, ms=models, client=client,
                resources=resources)


manager.add_command('db', MigrateCommand)
manager.add_command("shell", Shell(make_context=_make_context))


@manager.command
def add_user(email, password, confirm=True):
    """ Add a user to the database.
    email - A valid email address (primary login key)
    password - Any string
    """
    user = user_datastore.create_user(
        email=email, password=encrypt_password(password))
    if confirm:
        user.confirmed_at = datetime.datetime.now()
    db.session.commit()


@manager.command
def add_task(local_path, task, include_predictors=None,
             exclude_predictors=None, filters='{}', reingest=False):
    """ Add BIDS dataset to database.
    local_path - Path to local_path directory
    task - Task name
    include_predictors - Set of predictors to ingest. "None" ingests all.
    filters - string JSON object with optional run filters
    """
    populate.add_task(
        task, local_path=local_path, **json.loads(filters),
        include_predictors=include_predictors,
        exclude_predictors=exclude_predictors,
        reingest=reingest)


@manager.command
def extract_features(local_path, task, graph_spec, filters='{}'):
    """ Extract features from a BIDS dataset.
    local_path - Path to bids directory
    task - Task name
    graph_spec - Path to JSON pliers graph spec
    filters - string JSON object with optional run filters
    """
    populate.extract_features(
        local_path, task, graph_spec, **json.loads(filters))


@manager.command
def ingest_from_json(config_file, update_features=False, reingest=False):
    """ Ingest/update datasets and extracted features from a json config file.
    config_file - json config file detailing datasets and pliers graph_json
    automagic - Force enable datalad automagic
    """
    populate.ingest_from_json(
        config_file, update_features=update_features,
        reingest=reingest)


if __name__ == '__main__':
    manager.run()
