# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template

from flask_security import Security
from flask_jwt import JWT
from flask_restful import Api

from models import user_datastore

from resources.analyses import Analyses
from resources.datasets import Datasets
from resources.extractors import Extractors

from database import db
from auth import authenticate, load_user

app = Flask(__name__)
try:
    app.config.from_object(os.os.environ['APP_SETTINGS'])
except RuntimeError:
    app.config.from_object('config.DevelopmentConfig')

db.init_app(app)

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)

# Set up API routes
api = Api(app)
api.add_resource(Analyses, '/api/v1/analyses')
api.add_resource(Datasets, '/api/v1/datasets')
api.add_resource(Extractors, '/api/v1/extractors')

# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
    db.init_app(app)
    app.run()