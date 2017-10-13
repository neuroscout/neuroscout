# -*- coding: utf-8 -*-
""" Core Neuroscout App """
import os
from flask import Flask, send_file, render_template
from database import db

app = Flask(__name__, static_folder='/static')
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)

from flask_mail import Mail
mail = Mail(app)

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
        ('AnalysisRootResource', 'analyses'),
        ('AnalysisResource', 'analyses/<analysis_id>'),
        ('AnalysisFullResource', 'analyses/<analysis_id>/full'),
        ('CloneAnalysisResource', 'analyses/<analysis_id>/clone'),
        ('CompileAnalysisResource', 'analyses/<analysis_id>/compile'),
        ('AnalysisResourcesResource', 'analyses/<analysis_id>/resources'),
        ('AnalysisBundleResource', 'analyses/<analysis_id>/bundle'),
        ('DesignEventsResource', 'analyses/<analysis_id>/design/events'),
        # ('DesignEventsResource', 'analyses/<analysis_id>/design/events/tsv'),
        ('ResultResource', 'results/<int:result_id>'),
        ('RunListResource', 'runs'),
        ('RunResource', 'runs/<int:run_id>'),
        ('PredictorListResource', 'predictors'),
        ('PredictorResource', 'predictors/<int:predictor_id>'),
        ('PredictorEventListResource', 'predictor-events'),
        ('UserRootResource', 'user'),
        ('TaskResource', 'tasks/<int:task_id>'),
        ('TaskListResource', 'tasks')
    ])

@app.route('/')
def index():
    ''' Serve index '''
    return send_file("frontend/build/index.html")

@app.route('/confirm/<token>')
def confirm(token):
    ''' Serve confirmaton page '''
    expired, invalid, user = confirm_email_token_status(token)
    if not expired and not invalid:
        confirmed = confirm_user(user)
        db.session.commit()
    return render_template('confirm.html',
                           confirmed=confirmed, expired=expired, invalid=invalid,
                           email=user.email)

if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=app.config['DEBUG'], port=5001)
