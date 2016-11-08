# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
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

# Set up API routes
from flask_restful import Api
from resources.analysis import AnalysisResource, AnalysisListResource
from resources.dataset import DatasetResource, DatasetListResource
from resources.extractor import ExtractorResource, ExtractorListResource
from resources.result import ResultResource, ResultListResource
from resources.stimulus import StimulusResource, StimulusListResource
from resources.event  import PredictorResource, PredictorListResource

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
api.add_resource(StimulusResource, '/api/v1/stimuli/<stimulus_id>')

api.add_resource(PredictorListResource, '/api/v1/predictor')
api.add_resource(PredictorResource, '/api/v1/timelines/<predictor_id>')


# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
    db.init_app(app)
    app.run()