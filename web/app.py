# -*- coding: utf-8 -*-
import os
import logging

from flask import Flask, render_template, jsonify, request
from flask_security import Security
from flask_security.utils import encrypt_password, verify_password
from flask_jwt import JWT, jwt_required

from flask_restful import Resource, Api

from database import db
from models import Dataset, User, Analysis, Extractor, Timeline, \
	TimelineData, Result, Stimulus, Role, user_datastore

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)

api = Api(app)

# Setup Flask-Security
security = Security(app, user_datastore)

# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

# JWT Token authentication
def authenticate(username, password):
    user = user_datastore.find_user(email=username)
    if user and username == user.email and verify_password(password, user.password):
        return user
    return None

def load_user(payload):
    user = user_datastore.find_user(id=payload['identity'])
    return user

jwt = JWT(app, authenticate, load_user)

# API
class HelloWorld(Resource):
	@jwt_required()
	def get(self):
		return {'hello': 'world'}

api.add_resource(HelloWorld, '/api/v1')

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
    with app.app_context():
        db.create_all()
    app.run()

