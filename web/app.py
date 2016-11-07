# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template

from flask_security import Security
from flask_jwt import JWT
from flask_restful import Api

from models.auth import user_datastore

from resources.analyses import AnalysisResource, AnalysisListResource
from resources.datasets import DatasetResource, DatasetListResource
from resources.extractors import ExtractorResource, ExtractorListResource
from resources.results import ResultResource, ResultListResource
from resources.stimuli import StimulusResource, StimulusListResource
from resources.timelines import TimelineResource, TimelineListResource


from database import db
from auth import authenticate, load_user

app = Flask(__name__)
try:
    app.config.from_object(os.environ['APP_SETTINGS'])
except KeyError:
    app.config.from_object('config.DevelopmentConfig')
db.init_app(app)

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)

# Set up API routes
api = Api(app)
api.add_resource(AnalysisListResource, '/api/v1/analyses')
api.add_resource(AnalysisResource, '/api/v1/analyses/<analysis_id>')

api.add_resource(DatasetListResource, '/api/v1/datasets')
api.add_resource(DatasetResource, '/api/v1/datasets/<dataset_id>')

api.add_resource(ExtractorListResource, '/api/v1/extractors')
api.add_resource(ExtractorResource, '/api/v1/extractors/<extractor_id>')

api.add_resource(ResultListResource, '/api/v1/results')
api.add_resource(ResultResource, '/api/v1/results/<timeline_id>')

api.add_resource(StimulusListResource, '/api/v1/stimuli')
api.add_resource(StimulusResource, '/api/v1/stimuli/<stimuli_id>')

api.add_resource(TimelineListResource, '/api/v1/timelines')
api.add_resource(TimelineResource, '/api/v1/timelines/<timeline_id>')



# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
    db.init_app(app)
    app.run()