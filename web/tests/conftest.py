import os
import pytest
from flask_security.utils import encrypt_password
from core import app as _app
from database import db as _db

import sqlalchemy as sa

"""
Session / db managment tools
"""
@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    if 'APP_SETTINGS' in os.environ:
        if os.environ['APP_SETTINGS'] == 'config.config.DevelopmentConfig':
            _app.config.from_object('config.config.DockerTestConfig')
        elif os.environ['APP_SETTINGS'] != 'config.config.TravisConfig':
            _app.config.from_object('config.config.TestingConfig')
    else:
        _app.config.from_object('config..config.TestingConfig')

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
    """Creates a new db session for a test. Changes in session are rolled back"""
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
    from tests.request_utils import Client

    _ , ((email, password), _) = add_users
    client = Client(email=email, password=password)
    return client

"""
Data population fixtures
"""
from models import Analysis, Result, Predictor, User, Role
import populate

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data/datasets/bids_test')
YML_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data/test_dataset.yml')


@pytest.fixture(scope="function")
def add_users(app, db, session):
    """ Adds a test user to db """
    from flask_security import SQLAlchemyUserDatastore

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    user1 = 'test1@gmail.com'
    pass1 = 'test1'

    user2 = 'test2@gmail.com'
    pass2 = 'test2'

    user_datastore.create_user(email=user1, password=encrypt_password(pass1))
    session.commit()
    id_1 = user_datastore.find_user(email=user1).id

    user_datastore.create_user(email=user2, password=encrypt_password(pass2))
    session.commit()
    id_2 = user_datastore.find_user(email=user2).id

    yield (id_1, id_2), ((user1, pass1), (user2, pass2))


@pytest.fixture(scope="function")
def add_dataset(session):
    """ Add a dataset with two subjects """
    return populate.add_dataset(session, DATASET_PATH, 'bidstest',
                                verbose=False)


@pytest.fixture(scope="function")
def add_dataset_remote(session):
    """ Add a dataset with two subjects """
    return populate.ingest_from_yaml(session, YML_PATH,
                                     _app.config['DATASET_DIR'])[0]

@pytest.fixture(scope="function")
def add_analysis(session, add_users, add_dataset):
    analysis = Analysis(dataset_id = add_dataset, user_id = add_users[0][0],
        name = "My first fMRI analysis!", description = "Ground breaking")


    session.add(analysis)
    session.commit()

    return analysis.id

@pytest.fixture(scope="function")
def add_analysis_user2(session, add_users, add_dataset):
    analysis = Analysis(dataset_id = add_dataset, user_id = add_users[0][1],
        name = "My first fMRI analysis!", description = "Ground breaking")


    session.add(analysis)
    session.commit()

    return analysis.id


@pytest.fixture(scope="function")
def add_predictor(session, add_dataset):
    pred = Predictor(dataset_id = add_dataset,
        name = "RT")

    session.add(pred)
    session.commit()

    return pred.id

@pytest.fixture(scope="function")
def add_result(session, add_analysis):
    result = Result(analysis_id = add_analysis)

    session.add(result)
    session.commit()

    return result.id
