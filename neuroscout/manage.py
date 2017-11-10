"""
    Command line management tools.
"""
import os
import requests
import json
import datetime

from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_security.utils import encrypt_password

import populate
from core import app, db
from models import user_datastore

app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db, directory=app.config['MIGRATIONS_DIR'])
manager = Manager(app)

def _make_context():
	import models
	from tests.request_utils import Client
	import resources

	try:
		client = Client(requests, 'http://127.0.0.1:80',
			username='test2@test.com', password='password')
	except:
		client = None

	return dict(app=app, db=db, models=models, client=client,
		resources=resources)

manager.add_command('db', MigrateCommand)
manager.add_command("shell", Shell(make_context=_make_context))

@manager.command
def add_user(email, password, confirm=True):
    """ Add a user to the database.
    email - A valid email address (primary login key)
    password - Any string
    """
    user = user_datastore.create_user(
        email=email, password=encrypt_password(password))
    if confirm:
        user.confirmed_at = datetime.datetime.now()
    db.session.commit()

@manager.command
def add_task(local_path, task, replace=False, automagic=False,
	skip_predictors=False, filters='{}'):
	""" Add BIDS dataset to database.
	local_path - Path to local_path directory
	task - Task name
	replace - If dataset is already in db, re-ingest?
	automagic - Force enable datalad automagic
	skip_predictors - Skip original Predictors
	filters - string JSON object with optional run filters
	"""
	populate.add_task(db.session, task, local_path=local_path,
			 replace=replace, verbose=True, skip_predictors=skip_predictors,
			 automagic=automagic, **json.loads(filters))

@manager.command
def extract_features(local_path, task, graph_spec, filters='{}'):
	""" Extract features from a BIDS dataset.
	local_path - Path to bids directory
	task - Task name
	graph_spec - Path to JSON pliers graph spec
	filters - string JSON object with optional run filters
	"""
	populate.extract_features(db.session, local_path, task, graph_spec,
		verbose=True, **json.loads(filters))

## Need to modify or create new function for updating dataset
## e.g. dealing w/ IncompleteResultsError if cloning into existing dir
@manager.command
def ingest_from_json(config_file, replace=False, automagic=False):
	""" Ingest/update datasets and extracted features from a json config file.
	config_file - json config file detailing datasets and pliers graph_json
	replace - If dataset is already in db, re-ingest?
	automagic - Force enable datalad automagic
	"""
	populate.ingest_from_json(db.session, config_file, app.config['DATASET_DIR'],
		replace=replace, automagic=automagic)


if __name__ == '__main__':
    manager.run()
