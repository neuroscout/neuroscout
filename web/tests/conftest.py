import os
import pytest
from flask_security.utils import encrypt_password
from app import app, user_datastore
from database import db
import json 

@pytest.fixture(scope="session")
def db_init():
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

@pytest.fixture(scope="session")
def add_user():
    """ Adds a test user to db """

    user_name = 'test1'
    password = 'test1'

    with app.app_context():
        user_datastore.create_user(email=user_name, password=encrypt_password(password))
        db.session.commit()

    return user_name, password

@pytest.fixture(scope="session")
def valid_auth_resp(add_user):
    from tests.request_utils import Client
    client = Client()
    username, password = add_user
    
    return json.loads(client.auth(username, password).data.decode())