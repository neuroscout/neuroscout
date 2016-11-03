import os

from flask_security.utils import encrypt_password

if os.environ['APP_SETTINGS'] != 'config.TravisConfig':
    os.environ['APP_SETTINGS'] = 'config.TestingConfig'

from app import app, user_datastore
from database import db

import pytest

@pytest.fixture(scope="session")
def db_init():
    """" Fixture to initalize db, and clean up at the end of session """
    db.init_app(app)
    with app.app_context():
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