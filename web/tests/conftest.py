import os
import pytest
from flask_security.utils import encrypt_password
from app import app as _app
from database import db as _db

import sqlalchemy as sa

### Session / db managment tools
@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    if 'APP_SETTINGS' in os.environ:
        if os.environ['APP_SETTINGS'] != 'config.TravisConfig':
            _app.config.from_object('config.TestingConfig')
    else:
        _app.config.from_object('config.TestingConfig')

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

    _ , (username, password) = add_users
    client = Client(username=username, password=password)
    return client

### Data population fixtures
from models import (Analysis, Dataset, Predictor, Extractor, Stimulus,
					Result, ExtractedFeature, ExtractedEvent, Run)

@pytest.fixture(scope="function")
def add_users(app, db, session):
    """ Adds a test user to db """
    from flask_security import SQLAlchemyUserDatastore
    from models.auth import User, Role

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    user1 = 'test1@gmail.com'
    pass1 = 'test1'

    user_datastore.create_user(email=user1, password=encrypt_password(pass1))
    session.commit()
    id_1 = user_datastore.find_user(email=user1).id

    user_datastore.create_user(email='test2@gmail.com', password=encrypt_password('test2'))
    session.commit()
    id_2 = user_datastore.find_user(email='test2@gmail.com').id

    yield (id_1, id_2), (user1, pass1)

@pytest.fixture(scope="function")
def add_datasets(session):
    dataset = Dataset(name='ds39', task='moviewatching')
    session.add(dataset)
    session.commit()

    dataset_2 = Dataset(name='ds09', task='objectrecognition')
    session.add(dataset_2)
    session.commit()

    return [dataset.id, dataset_2.id]

@pytest.fixture(scope="function")
def add_run(session, add_datasets):
    run = Run(subject=1, dataset_id=add_datasets[0])
    session.add(run)
    session.commit()

    return run.id

@pytest.fixture(scope="function")
def add_analyses(session, add_users, add_datasets):
    analysis = Analysis(dataset_id = add_datasets[0], user_id = add_users[0][0],
        name = "My first fMRI analysis!", description = "Ground breaking")

    analysis_2 = Analysis(dataset_id = add_datasets[0], user_id = add_users[0][1],
        name = "fMRI is cool" , description = "Earth shattering")

    session.add(analysis)
    session.commit()

    session.add(analysis_2)
    session.commit()

    return [analysis.id, analysis_2.id]

@pytest.fixture(scope="function")
def add_result(session, add_analyses):
    result = Result(analysis_id = add_analyses[0])

    session.add(result)
    session.commit()

    return result.id

@pytest.fixture(scope="function")
def add_stimulus(session, add_run):
    stim = Stimulus(path='/some/stim', sha1_hash='i9j23inf3f')

    session.add(stim)
    session.commit()

    return stim.id

@pytest.fixture(scope="function")
def add_extracted_feature(session):
    extracted_feature = ExtractedFeature(description="Something")
    session.add(extracted_feature)
    session.commit()

    return extracted_feature.id

@pytest.fixture(scope="function")
def add_extracted_event(session, add_extracted_feature, add_stimulus):
    extracted_feature = ExtractedEvent(onset=0, duration=1, value=1,
                        stimulus_id=add_stimulus,
                        extracted_feature_id=add_extracted_feature)

    session.add(extracted_feature)
    session.commit()

    return extracted_feature.id

@pytest.fixture(scope="function")
def add_predictor(session, add_run):
    predictor = Predictor(name='rt', run_id=add_run)

    session.add(predictor)
    session.commit()

    return predictor.id
