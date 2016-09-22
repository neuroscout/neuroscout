# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from database import db
from api import api
from flask_security import Security, SQLAlchemyUserDatastore, login_required
import logging


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(api, url_prefix='/api')

db.init_app(app)

from models import Dataset, User, Analysis, Extractor, Timeline, TimelineData, Result, Stimulus, Role

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)

### Create fixtures to make fake data, andd customize these ugly templates
# @app.before_first_request
# def create_user():
#     user_datastore.create_user(email='delavega@utexas.edu', password='password')
#     db.session.commit()

@app.route('/')
@login_required
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
	app.run()