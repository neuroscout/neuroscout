from database import db
from flask import current_app

class Dataset(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	analyses = db.relationship('Analysis', backref='dataset',
                                lazy='dynamic')
	stimuli = db.relationship('Stimulus', backref='dataset',
                                lazy='dynamic')
class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)  
	analyses = db.relationship('Analysis', backref='user',
                                lazy='dynamic')
class Analysis(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	results = db.relationship('Result', backref='analysis',
                                lazy='dynamic')]
	predictors = db.relationship('Predictor', backref='analysis',
                                lazy='dynamic')
class Extractor(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	predictors = db.relationship('Predictor', backref='extractor',
                                lazy='dynamic')
class Predictor(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	extractor_id = db.Column(db.Integer, db.ForeignKey('extractor.id'))
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
	stimuli_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
class Result(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
class Stimulus(db.Mode):
	id = db.Column(db.Integer, primary_key=True)
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	analyses = db.relationship('Predictor', backref='stimulus',
                                lazy='dynamic')

### Many to many between analysis and predictor
# Many to many:
# class App(db.Model):
# 	id = db.Column(db.Integer, primary_key=True) 