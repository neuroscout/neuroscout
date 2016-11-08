from database import db

class Predictor(db.Model):
	""" Combination of stimulus and predictor, with specific parameterization"""
	id = db.Column(db.Integer, primary_key=True) 
	stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
	extractor_id = db.Column(db.Integer, db.ForeignKey('extractor.id'))
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

	events = db.relationship('Event', backref='analysis',
                                lazy='dynamic')

	### Other meta-data will go here

class Event(db.Model):
	"""" Extracted feature events. Onsets are relative to the stimulus, not
	subject """
	id = db.Column(db.Integer, primary_key=True) 
	onset = db.Column(db.Integer) 
	duration = db.Column(db.Integer) 
	amplitude = db.Column(db.Integer) 

	predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'))
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
	stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
