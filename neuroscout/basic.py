""" Basic Flask app creation """
from .database import db
from flask import Flask
import os


def create_app():
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
    return app
