import os
import pytest
from flask_security.utils import encrypt_password
from app import app, user_datastore
from database import db

@pytest.fixture(scope="function")
def db_init_clean():
    """" Fixture to initalize db, and clean up at the end of session """
    db.init_app(app)
    with app.app_context():
        # Check if in testing mode, if not set to
        if 'APP_SETTINGS' in os.environ:
            if os.environ['APP_SETTINGS'] != 'config.TravisConfig':
                app.config.from_object('config.TestingConfig')
        else:
            app.config.from_object('config.TestingConfig')

        db.create_all()
        db.session.commit()

    yield 

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope="function")
def add_users():
    """ Adds a test user to db """

    user1 = 'test1'
    pass1 = 'test1'

    with app.app_context():
        user_datastore.create_user(email=user1, password=encrypt_password(pass1))
        db.session.commit()

        user_datastore.create_user(email='test2', password=encrypt_password('test2'))
        db.session.commit()

    return user1, pass1

@pytest.fixture(scope="function")
def auth_client(add_users):
    from tests.request_utils import Client
    client = Client()
    username, password = add_users
    client.auth(username, password)
    return client