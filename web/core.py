# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from database import db

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)

from flask_jwt import JWT
from flask_security import Security
from auth import authenticate, load_user, add_auth_to_swagger
from models import *

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)

# Enable CORS
from flask_cors import CORS
cors = CORS(app, resources={r"/api/*": {"origins": "*"},
                            r"/auth": {"origins": "*"},
                            r"/swagger/": {"origins": "*"}})

# Setup API
from apispec import APISpec
from flask_apispec.extension import FlaskApiSpec
from utils import route_factory

spec = APISpec(
    title='neuroscout',
    version='v1',
    plugins=['apispec.ext.marshmallow'],
)
app.config.update({
    'APISPEC_SPEC': spec})
add_auth_to_swagger(spec)

docs = FlaskApiSpec(app)
route_factory(app, docs,
    [
        ('DatasetResource', 'datasets/<int:dataset_id>'),
        ('DatasetListResource', 'datasets'),
        ('AnalysisListResource', 'analyses'),
        ('CreateAnalysisResource', 'analyses'),
        ('AnalysisResource', 'analyses/<analysis_id>'),
        ('CloneAnalysisResource', 'analyses/<analysis_id>/clone'),
        ('ResultResource', 'results/<int:result_id>'),
        ('RunListResource', 'runs'),
        ('RunResource', 'runs/<int:run_id>'),
        ('PredictorListResource', 'predictors'),
        ('PredictorResource', 'predictors/<int:predictor_id>'),
        ('PredictorEventListResource', 'predictor-events'),
        ('PredictorEventResource', 'predictor-events/<int:pe_id>'),
        ('UserResource', 'user'),
        ('UserPostResource', 'user'),
        ('TaskResource', 'tasks/<int:task_id>'),
        ('TaskListResource', 'tasks')
    ])

@app.route('/')
def index():
    ''' Serve SPA '''
    return render_template('default.html')

if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=app.config['DEBUG'], port=5001)
