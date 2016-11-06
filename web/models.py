from database import db
from sqlalchemy.dialects.postgresql import JSON
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

## Authentication
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(255))
    current_login_ip = db.Column(db.String(255))
    login_count = db.Column(db.Integer)

    def __repr__(self):
        return '<models.User[email=%s]>' % self.email

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class Dataset(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	analyses = db.relationship('Analysis', backref='dataset',
                                lazy='dynamic')
	stimuli = db.relationship('Stimulus', backref='dataset',
                                lazy='dynamic')
	attributes = db.Column(JSON) ## BIDS specification
	name = db.Column(db.String(30))
	external_id = db.Column(db.String(30), unique=True)
	events = db.Column(db.Text()) # TSV events file

# class Subject

# class Run
class Analysis(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	results = db.relationship('Result', backref='analysis',
                                lazy='dynamic')
	name = db.Column(db.String(30))
	description = db.Column(db.String(30))
	timelines = db.relationship('Timeline', backref='analysis',
                                lazy='dynamic')
	parent = db.Column(db.String(30))


class Extractor(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	timelines = db.relationship('Timeline', backref='extractor',
                                lazy='dynamic')
	name = db.Column(db.String(30))
	description = db.Column(db.String(30))
	version = db.Column(db.Float(10))
	input_type = db.Column(db.String(20))
	output_type  = db.Column(db.String(20))

class Timeline(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	extractor_id = db.Column(db.Integer, db.ForeignKey('extractor.id'))
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
	stimuli_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))

class TimelineData(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	timeline_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
	onset = db.Column(db.Float(10))
	amplitude = db.Column(db.Float(10))
	duration = db.Column(db.Float(10))

class Result(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

class Stimulus(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	timelines = db.relationship('Timeline', backref='stimulus',
                                lazy='dynamic')


### Many to many between analysis and predictor
# Many to many:
# class App(db.Model):
# 	id = db.Column(db.Integer, primary_key=True) 