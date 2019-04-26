# -*- coding: utf-8 -*-
""" Core Neuroscout App """
import os
from flask import Flask, send_file, render_template, url_for
from database import db

app = Flask(__name__, static_folder='/static')
app.config.from_object(os.environ['APP_SETTINGS'])
app.config.update(
    FEATURE_DATASTORE=str(app.config['FILE_DIR'] / 'feature-tracking.csv'),
    CACHE_DIR=str(app.config['FILE_DIR'] / 'cache'),
    STIMULUS_DIR=str(app.config['FILE_DIR'] / 'stimuli'),
    EXTRACTION_DIR=str(app.config['FILE_DIR'] / 'extracted'),
    FEATURE_SCHEMA=str(app.config['CONFIG_PATH'] / 'feature_schema.json'),
    PREDICTOR_SCHEMA=str(app.config['CONFIG_PATH'] / 'predictor_schema.json'),
    ALL_TRANSFORMERS=str(app.config['CONFIG_PATH'] / 'transformers.json'),
    BIBLIOGRAPHY=str(app.config['CONFIG_PATH'] / 'bibliography.json')
)


db.init_app(app)

from flask_mail import Mail
mail = Mail(app)

from flask_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': app.config['CACHE_DIR']})
cache.init_app(app)

from flask_jwt import JWT
from flask_security import Security
from flask_security.confirmable import confirm_email_token_status, confirm_user
from auth import authenticate, load_user, add_auth_to_swagger
from models import *

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)

# Enable CORS
from flask_cors import CORS
cors = CORS(app, resources={r"/api/*": {"origins": "*"},
                            r"/swagger/": {"origins": "*"}})

# Setup API
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from utils import route_factory

file_plugin = MarshmallowPlugin()
spec = APISpec(
    title='neuroscout',
    version='v1',
    plugins=[file_plugin],
    openapi_version='2.0'
)
app.config.update({
    'APISPEC_SPEC': spec})
add_auth_to_swagger(spec)

docs = FlaskApiSpec(app)
route_factory(
    app, docs,
    [
        ('DatasetResource', 'datasets/<int:dataset_id>'),
        ('DatasetListResource', 'datasets'),
        ('AnalysisRootResource', 'analyses'),
        ('AnalysisResource', 'analyses/<analysis_id>'),
        ('AnalysisFullResource', 'analyses/<analysis_id>/full'),
        ('AnalysisUploadResource', 'analyses/<analysis_id>/upload'),
        ('BibliographyResource', 'analyses/<analysis_id>/bibliography'),
        ('CloneAnalysisResource', 'analyses/<analysis_id>/clone'),
        ('CompileAnalysisResource', 'analyses/<analysis_id>/compile'),
        ('ReportResource', 'analyses/<analysis_id>/report'),
        ('AnalysisResourcesResource', 'analyses/<analysis_id>/resources'),
        ('AnalysisBundleResource', 'analyses/<analysis_id>/bundle'),
        ('AnalysisFillResource', 'analyses/<analysis_id>/fill'),
        ('RunListResource', 'runs'),
        ('RunResource', 'runs/<int:run_id>'),
        ('PredictorListResource', 'predictors'),
        ('PredictorResource', 'predictors/<int:predictor_id>'),
        ('PredictorEventListResource', 'predictor-events'),
        ('UserRootResource', 'user'),
        ('UserTriggerResetResource', 'user/reset_password'),
        ('UserResetSubmitResource', 'user/submit_token'),
        ('UserResendConfirm', 'user/resend_confirmation'),
        ('TaskResource', 'tasks/<int:task_id>'),
        ('TaskListResource', 'tasks')
    ])


@app.route('/confirm/<token>')
def confirm(token):
    ''' Serve confirmaton page '''
    expired, invalid, user = confirm_email_token_status(token)
    name = None
    confirmed = None
    if user:
        if not expired and not invalid:
            confirmed = confirm_user(user)
            db.session.commit()
        name = user.name
    else:
        confirmed = None
    return render_template('confirm.html',
                           confirmed=confirmed, expired=expired,
                           invalid=invalid, name=name,
                           action_url=url_for('index', _external=True))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    ''' Serve index '''
    return send_file("frontend/build/index.html")
