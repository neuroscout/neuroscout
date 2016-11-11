import os
import pytest
from flask_security.utils import encrypt_password
from app import app as _app
from app import user_datastore
from database import db as _db

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
    """Creates a new user_datastorebase session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture(scope="function")
def add_users(session):
    """ Adds a test user to db """

    user1 = 'test1'
    pass1 = 'test1'

    user_datastore.create_user(email=user1, password=encrypt_password(pass1))
    session.commit()

    user_datastore.create_user(email='test2', password=encrypt_password('test2'))
    session.commit()

    return user1, pass1

@pytest.fixture(scope="function")
def auth_client(add_users):
    from tests.request_utils import Client
    client = Client()
    username, password = add_users
    client.auth(username, password)
    return client