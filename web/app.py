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

from models import *

# Setup Flask-Security and JWT
security = Security(app, user_datastore)
jwt = JWT(app, authenticate, load_user)


from resources.analysis import AnalysisResource, AnalysisListResource
from resources.dataset import DatasetResource, DatasetListResource
# from resources.result import ResultResource, ResultListResource
# from resources.run import RunResource, RunListResource
# from resources.stimulus import StimulusResource
# from resources.predictor  import PredictorResource, PredictorListResource
# from resources.user  import UserResource

app.add_url_rule('/api/analyses', view_func=AnalysisListResource.as_view('analyses'))
app.add_url_rule('/api/analyses/<int:analysis_id>', view_func=AnalysisResource.as_view('analysis'))

app.add_url_rule('/api/datasets', view_func=DatasetListResource.as_view('datasets'))
app.add_url_rule('/api/datasets/<int:dataset_id>', view_func=DatasetResource.as_view('dataset'))


# Serve SPA
@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
    db.init_app(app)
    app.run(debug=app.config['DEBUG'])
