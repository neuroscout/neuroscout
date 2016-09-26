# -*- coding: utf-8 -*-
import os

from flask import Flask, render_template

from flask_security import Security
from flask_security.utils import encrypt_password
from flask_jwt import JWT

from flask_restful import Api
from resources.helloworld import HelloWorld

from database import db
from models import Dataset, User, Analysis, Extractor, Timeline, \
	TimelineData, Result, Stimulus, Role, user_datastore
from auth import authenticate, load_user

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)

api = Api(app)
# Set up API routes
api.add_resource(HelloWorld, '/api/v1/hello')

# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

# Bootstrap 
def create_test_models():
    user_datastore.create_user(email='test', password=encrypt_password('test'))
    user_datastore.create_user(email='test2', password=encrypt_password('test2'))

    db.session.commit()

@app.before_first_request
def bootstrap_app():
    if not app.config['TESTING']:
        if db.session.query(User).count() == 0:
            create_test_models()


# Start server 
if __name__ == '__main__':
    db.init_app(app)
    app.run()