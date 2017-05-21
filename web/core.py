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
        ('AnalysisRootResource', 'analyses'),
        ('AnalysisResource', 'analyses/<analysis_id>'),
        ('CloneAnalysisResource', 'analyses/<analysis_id>/clone'),
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
    ''' Serve SPA '''
    return render_template('default.html')

from worker import celery_app
import celery.states as states

import os
from flask import Flask
from flask import url_for

@app.route('/add/<int:param1>/<int:param2>')
def add(param1,param2):
    task = celery_app.send_task('mytasks.add', args=[param1, param2], kwargs={})
    return "<a href='{url}'>check status of {id} </a>".format(id=task.id,
                url=url_for('check_task',id=task.id,_external=True))

@app.route('/check/<string:id>')
def check_task(id):
    res = celery_app.AsyncResult(id)
    if res.state==states.PENDING:
        return res.state
    else:
        return str(res.result)

if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=app.config['DEBUG'], port=5001)
