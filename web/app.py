# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, jsonify
from database import db
# from api import api
from flask_security import Security, login_required, \
auth_token_required
import logging
from models import Dataset, User, Analysis, Extractor, Timeline, \
TimelineData, Result, Stimulus, Role, user_datastore

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

db.init_app(app)

# Setup Flask-Security
security = Security(app, user_datastore)

@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

@app.route('/dummy-api/', methods=['GET'])
@auth_token_required
def dummyAPI():
    ret_dict = {
        "Key1": "Value1",
        "Key2": "value2"
    }
    return jsonify(items=ret_dict)



if __name__ == '__main__':
	app.run()
