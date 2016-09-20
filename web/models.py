from database import db
from flask import current_app

class Dataset(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	analyses = db.relationship('Analysis', backref='dataset',
                                lazy='dynamic')
	stimuli = db.relationship('Stimulus', backref='dataset',
                                lazy='dynamic')
	metadata = db.Column(db.JSON) ## BIDS specification
	name = db.Column(db.String(30))
	external_id = db.Column(db.String(30))
	events = db.Column(db.Text()) # TSV events file

# class Subject

# class Run

class User(db.Model):
	""" Mostly authentication stuff for now """
	id = db.Column(db.Integer, primary_key=True)  
	analyses = db.relationship('Analysis', backref='user',
                                lazy='dynamic')
	name = db.Column(db.String(30))
	# email ## Do I need this?
	# institution
	# password ## OpenID

class Analysis(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	results = db.relationship('Result', backref='analysis',
                                lazy='dynamic')]
	name = db.Column(db.String(30))
	description = db.Column(db.String(30))
	predictors = db.relationship('Predictor', backref='analysis',
                                lazy='dynamic')
	parent = db.Column(db.String(30))


class Extractor(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	predictors = db.relationship('Predictor', backref='extractor',
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
	analyses = db.relationship('Predictor', backref='stimulus',
                                lazy='dynamic')


### Many to many between analysis and predictor
# Many to many:
# class App(db.Model):
# 	id = db.Column(db.Integer, primary_key=True) 