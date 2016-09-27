import os

from flask_security.utils import encrypt_password

from app import app, user_datastore
from database import db

import pytest

@pytest.fixture(scope="session")
def flask_init():
    if os.environ['APP_SETTINGS'] != 'config.TravisConfig':
        app.config.from_object('config.TestingConfig')

    db.init_app(app)
    with app.app_context():
        db.create_all()
        user_datastore.create_user(email='test1', password=encrypt_password('test1'))
        print("CREATING USER")
        db.session.commit()

    yield 

    with app.app_context():
        db.session.remove()
        db.drop_all()
