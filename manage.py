"""
    Command line management tools.
"""
import os
import requests
import datetime

from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_security.utils import encrypt_password

from neuroscout import populate
from neuroscout.core import app, db
from neuroscout.models import user_datastore
from neuroscout import models
from neuroscout.tests import conftest

app.config.from_object(os.environ['APP_SETTINGS'])
migrate = Migrate(app, db, directory=app.config['MIGRATIONS_DIR'])
manager = Manager(app)


def _make_context():
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
def setup_dataset(preproc_address, raw_address=None, path=None,
                  setup_preproc=True, url=None, summary=None,
                  dataset_name=None, long_description=None, tasks=None):
    """ Installs Dataset using DataLad (unless a dataset_path is given),
    links preproc and raw dataset, and creates a template config file
    for the dataset.

    Args:
       preproc_address: DataLad address of a fmripreprocessed dataset
       dataset_address: DataLad address to raw dataset
       path: path on disk to raw BIDS dataset. If provided,
                     `dataset_address` is optional.
       setup_preproc: Install preproc dataset, and symlink in raw dataset
       url: URL to dataset information
       dataset_summary: Short summary of dataset
       long_description: Longer description of dataset
       tasks: List of tasks to include in config file

    Returns:
       path to template config_file """
    populate.setup_dataset(
        preproc_address, raw_address, path, setup_preproc, url,
        summary, long_description, tasks)


@manager.command
def ingest_from_json(config, reingest=False):
    """ Ingest/update datasets and extracted features from a json config file.
    config_file - json config file detailing datasets and pliers graph_json
    automagic - Force enable datalad automagic
    """
    populate.ingest_from_json(config, reingest=reingest)


@manager.command
def extract_features(extractor_graphs, dataset_name=None, task_name=None,
                     resample_frequency=None):
    """ Extract features from a BIDS dataset.
    extractor_graphs - List of Graphs to apply to relevant stimuli
    dataset_name - Dataset name - By default applies to all active datasets
    task - Task name
    resample_frequency - None
    """
    populate.extract_features(
        extractor_graphs, dataset_name, task_name,
        resample_frequency=resample_frequency)


@manager.command
def setup_test_db():
    # Only run if in setup mode
    if not app.config['TESTING']:
        raise Exception("This fixture can only be run in test mode")

    # Init db
    db.init_app(app)
    db.create_all()

    # Create test users
    users = [('user@example.com', 'string', 'testuser'),
             ('test2@gmail.com', 'test2', 'testuser2')]

    for email, password, name in users:
        user_datastore.create_user(
            email=email, password=encrypt_password(password),
            user_name=name, confirmed_at=datetime.datetime.now())
        db.session.commit()

    id_1 = user_datastore.find_user(email=users[0][0]).id

    dataset_id = populate.add_task(
        'bidstest', local_path=conftest.DATASET_PATH)

    predictor_id = populate.extract_features(
        conftest.EXTRACTORS, 'Test Dataset', 'bidstest')

    analysis_id = conftest.add_analysis_abstract(db.session, id_1, dataset_id)

    pred = models.Predictor(dataset_id=dataset_id, name="RT")

    db.session.add(pred)
    db.session.commit()


@manager.command
def teardown_test_db():
    # Only run if in setup mode
    if not app.config['TESTING']:
        raise Exception("This fixture can only be run in test mode")

    db.session.remove()
    db.drop_all()


if __name__ == '__main__':
    manager.run()
