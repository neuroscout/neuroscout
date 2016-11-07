from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app import app, db
import os
import requests

app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db)
manager = Manager(app)

def _make_context():
	import models
	from tests.request_utils import Client
	import resources

	client = Client(requests, 'http://127.0.0.1:5000', username='test', password='test')

	return dict(app=app, db=db, models=models, client=client, 
		resources=resources)

manager.add_command('db', MigrateCommand)
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == '__main__':
    manager.run()
