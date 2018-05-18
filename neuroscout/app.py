import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

""" Set up app and database """

app = Flask(__name__, static_folder='/static')
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy()
db.init_app(app)
