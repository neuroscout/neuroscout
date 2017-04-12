from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app import app, db
import os
import requests
import populate

app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db)
manager = Manager(app)

def _make_context():
	import models
	from tests.request_utils import Client
	import resources

	client = Client(requests, 'http://127.0.0.1:5000',
		username='test2@test.com', password='password')

	return dict(app=app, db=db, models=models, client=client,
		resources=resources)

manager.add_command('db', MigrateCommand)
manager.add_command("shell", Shell(make_context=_make_context))

@manager.command
def add_user(email, password):
    from models import user_datastore
    from flask_security.utils import encrypt_password

    user_datastore.create_user(email=email, password=encrypt_password(password))
    db.session.commit()

@manager.command
def add_dataset(bids_path, task, replace=False, verbose=True, **kwargs):
	populate.add_dataset(db.session, bids_path, task, replace=False,
						 verbose=verbose, **kwargs)

@manager.command
def extract_features(bids_path, graph_spec,  verbose=True, **kwargs):
	populate.extract_features(db.session, bids_path, graph_spec,
							  verbose=verbose, **kwargs)

if __name__ == '__main__':
    manager.run()
