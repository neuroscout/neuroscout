from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
import ConfigParser 
from app import app, db
import os

app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db, compare=True)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
