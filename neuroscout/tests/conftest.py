from os import environ, makedirs
from pathlib import Path
import pytest
from flask_security.utils import encrypt_password
from ..core import app as _app
from ..database import db as _db
import datetime
import sqlalchemy as sa
from ..models import (Analysis, Predictor,
                      PredictorRun, User, Role, Dataset)
from .. import populate

"""
Session / db management tools
"""


@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    if 'APP_SETTINGS' not in environ:
        _app.config.from_object('config.app.TestingConfig')

    makedirs(_app.config['FILE_DIR'] / 'predictor_collections', exist_ok=True)
    makedirs(_app.config['FILE_DIR'] / 'analyses', exist_ok=True)
    makedirs(_app.config['FILE_DIR'] / 'reports', exist_ok=True)

    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database."""
    _db.init_app(app)
    _db.create_all()

    yield _db

    _db.session.remove()
    _db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    """Creates a new db session for a test.
    Changes in session are rolled back """
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    session.begin_nested()

    # session is actually a scoped_session
    # for the `after_transaction_end` event, we need a session instance to
    # listen for, hence the `session()` call
    @sa.event.listens_for(session(), 'after_transaction_end')
    def resetart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            session.expire_all()
            session.begin_nested()

    db.session = session

    yield session

    session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def auth_client(add_users):
    """ Return authorized client wrapper """
    from .request_utils import Client

    _, ((email, password), _) = add_users
    client = Client(email=email, password=password)
    return client


"""
Data population fixtures
"""


DATA_PATH = Path(__file__).resolve().parents[0] / 'data'

DATASET_PATH = DATA_PATH / 'bids_test'
LOCAL_JSON_PATH = (DATA_PATH / 'test_local.json').as_posix()
REMOTE_JSON_PATH = (DATA_PATH / 'test_remote.json').as_posix()
EXTRACTORS = [
    [{"transformer": "BrightnessExtractor"}],
    [{"transformer": "VibranceExtractor"}]
    ]


@pytest.fixture()
def get_data_path():
    return DATA_PATH


@pytest.fixture(scope="function")
def add_users(app, db, session):
    """ Adds a test user to db """
    from flask_security import SQLAlchemyUserDatastore

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    user1 = 'test1@gmail.com'
    pass1 = 'test1'

    user2 = 'test2@gmail.com'
    pass2 = 'test2'

    user_datastore.create_user(email=user1, password=encrypt_password(pass1),
                               user_name='testuser',
                               confirmed_at=datetime.datetime.now())
    session.commit()
    id_1 = user_datastore.find_user(email=user1).id

    user_datastore.create_user(email=user2, password=encrypt_password(pass2),
                               user_name='testuser2',
                               confirmed_at=datetime.datetime.now())
    session.commit()
    id_2 = user_datastore.find_user(email=user2).id

    yield (id_1, id_2), ((user1, pass1), (user2, pass2))


@pytest.fixture(scope="function")
def add_task(session):
    """ Add a dataset with two subjects """
    dataset_id = populate.add_dataset(
      'Test Dataset',
      'example dataset',
      '///datalad/preproc/address',
      DATASET_PATH
    )

    populate.add_task('bidstest', 'Test Dataset', DATASET_PATH)
    return dataset_id


@pytest.fixture(scope="function")
def add_task_remote(session):
    """ Add a dataset with two subjects. """
    config_path = populate.setup_dataset(
      '///fake/dataset', 
      raw_address='https://github.com/adelavega/bids_test', 
      dataset_summary="A test dataset", 
      skip_preproc=True, 
      url="https://github.com/adelavega/bids_test", subject="01", run=1
      )

    return populate.ingest_from_json(config_path)


@pytest.fixture(scope="function")
def add_local_task_json(session):
    """ Add a dataset with two subjects. """
    config_path = populate.setup_dataset(
      '///fake/dataset', 
      path="./neuroscout/tests/data/bids_test",
      dataset_summary="A test dataset",
      skip_preproc=True, 
      url="https://github.com/adelavega/bids_test", subject="01", run=1
      )
    return populate.ingest_from_json(config_path)


@pytest.fixture(scope="function")
def extract_features(session, add_task):
    return populate.extract_features(EXTRACTORS, 'Test Dataset', 'bidstest')


@pytest.fixture(scope="function")
def reextract(session, extract_features):
    return populate.extract_features(EXTRACTORS, 'Test Dataset', 'bidstest')


def add_analysis_abstract(session, user_id, dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id).first()

    analysis = Analysis(
        dataset_id=dataset_id, user_id=user_id,
        name="My first fMRI analysis!", description="Ground breaking",
        runs=dataset.runs)

    run_id = [r.id for r in dataset.runs]
    pred_id = PredictorRun.query.filter(
        PredictorRun.run_id.in_(run_id)).distinct(
            'predictor_id').with_entities('predictor_id').all()

    analysis.predictors = Predictor.query.filter(
        Predictor.id.in_(pred_id),
        Predictor.name.in_(['Brightness', 'rt'])).all()

    analysis.model = {
        "Name": "test_model1",
        "Description": "this is a sample",
        "Input": {
          "task": "bidstest",
          "subject": ["01", "02"]
        },
        "Steps": [
          {
            "Level": "Run",
            "Transformations": [
              {
                "Name": "Scale",
                "Input": [
                  "Brightness"
                ]
              }
            ],
            "Model": {
              "X": [
                "Brightness",
                "rt"
              ]
            },
            "Contrasts": [
              {
                "Name": "BvsRT",
                "ConditionList": [
                  "Brightness",
                  "rt"
                ],
                "Weights": [
                  1,
                  -1
                ],
                "Type": "T"
              }
            ]
          },
          {
            "Level": "Subject",
            "Model": {
              "X": [
                "BvsRT"
              ]
            },
          }
        ]
      }

    session.add(analysis)
    session.commit()

    return analysis.id


@pytest.fixture(scope="function")
def add_analysis(session, add_users, add_task, extract_features):
    user_id = add_users[0][0]
    return add_analysis_abstract(session, user_id, add_task)


@pytest.fixture(scope="function")
def add_analysis_fail(session, add_users, add_task):
    """ This analysis is from user 1 should fail compilation """
    dataset = Dataset.query.filter_by(id=add_task).first()
    analysis = Analysis(dataset_id=add_task, user_id=add_users[0][0],
                        name="A bad analysis!", description="Bad!",
                        runs=dataset.runs)

    session.add(analysis)
    session.commit()

    return analysis.id


@pytest.fixture(scope="function")
def add_analysis_user2(session, add_users, add_task):
    """ This analysis is from user 2 and also should fail compilation """
    dataset = Dataset.query.filter_by(id=add_task).first()
    analysis = Analysis(
        dataset_id=add_task, user_id=add_users[0][1],
        name="My first fMRI analysis!", description="Ground breaking",
        runs=dataset.runs)

    session.add(analysis)
    session.commit()

    return analysis.id


@pytest.fixture(scope="function")
def add_predictor(session, add_task):
    pred = Predictor(dataset_id=add_task, name="RT")

    session.add(pred)
    session.commit()

    return pred.id
