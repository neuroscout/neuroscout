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