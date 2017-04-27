# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, jsonify
from database import db

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)

from flask_jwt import JWT
from flask_security import Security
from models.auth import user_datastore
from auth import authenticate, load_user

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)

# Setup apispec
from apispec import APISpec
from flask_apispec.extension import FlaskApiSpec

app.config.update({
    'APISPEC_SPEC': APISpec(
        title='neuroscout',
        version='v1',
        plugins=['apispec.ext.marshmallow'],
    )})

docs = FlaskApiSpec(app)

# Enable CORS
from flask_cors import CORS
cors = CORS(app, resources={r"/api/*": {"origins": "*"},
                            r"/swagger/": {"origins": "*"}})

from models import *

from resources.analysis import (AnalysisResource, AnalysisListResource,
                                AnalysisPostResource)
from resources.dataset import DatasetResource, DatasetListResource
# from resources.result import ResultResource, ResultListResource
from resources.run import RunResource, RunListResource
# from resources.stimulus import StimulusResource
# from resources.predictor  import PredictorResource, PredictorListResource
# from resources.user  import UserResource


app.add_url_rule('/api/datasets', view_func=DatasetListResource.as_view('datasetlistresource'))
app.add_url_rule('/api/datasets/<int:dataset_id>', view_func=DatasetResource.as_view('datasetresource'))

docs.register(DatasetListResource)
docs.register(DatasetResource)

app.add_url_rule('/api/analyses', view_func=AnalysisListResource.as_view('analysislistresource'))
app.add_url_rule('/api/analyses', view_func=AnalysisPostResource.as_view('analysispostresource'))
app.add_url_rule('/api/analyses/<int:analysis_id>', view_func=AnalysisResource.as_view('analysisresource'))

docs.register(AnalysisPostResource)
docs.register(AnalysisListResource)
docs.register(AnalysisResource)

app.add_url_rule('/api/runs', view_func=RunListResource.as_view('runlistresource'))
app.add_url_rule('/api/runs/<int:run_id>', view_func=RunResource.as_view('runresource'))

docs.register(RunListResource)
docs.register(RunResource)

# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=app.config['DEBUG'])
