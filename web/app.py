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
from flask_restful_swagger import swagger

from resources.analysis import AnalysisResource, AnalysisListResource
from resources.dataset import DatasetResource, DatasetListResource
from resources.extractor import ExtractorResource, ExtractorListResource
from resources.result import ResultResource, ResultListResource
from resources.stimulus import StimulusResource
from resources.predictor  import PredictorResource, PredictorListResource
from resources.user  import UserResource

api = swagger.docs(Api(app), apiVersion='0.1')

api.add_resource(AnalysisListResource, '/api/analyses')
api.add_resource(AnalysisResource, '/api/analyses/<analysis_id>')

api.add_resource(DatasetListResource, '/api/datasets')
api.add_resource(DatasetResource, '/api/datasets/<dataset_id>')

api.add_resource(ExtractorListResource, '/api/extractors')
api.add_resource(ExtractorResource, '/api/extractors/<extractor_id>')

api.add_resource(ResultListResource, '/api/results')
api.add_resource(ResultResource, '/api/results/<timeline_id>')

api.add_resource(StimulusResource, '/api/stimuli/<stimulus_id>')

api.add_resource(PredictorListResource, '/api/predictor')
api.add_resource(PredictorResource, '/api/predictor/<predictor_id>')

api.add_resource(UserResource, '/api/user')


# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
    db.init_app(app)
    app.run()