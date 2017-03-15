from database import db

# Need to add join table between Predictor and Analysis

class Predictor(db.Model):
	""" Instantiation of a predictor in a run, with run specific
		onsets.

		A collection of PredictorEvents.

	 	Also, joins Analysis and Run. """
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text, nullable=False)
	description = db.Column(db.Text)

	run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)

	predictor_events = db.relationship('PredictorEvent', backref='predictor',
								lazy='dynamic')

class PredictorEvent(db.Model):
	""" An event within a Predictor. Onset is relative to run. """
	id = db.Column(db.Integer, primary_key=True)
	onset = db.Column(db.Float, nullable=False)
	duration = db.Column(db.Float)
	value = db.Column(db.Float, nullable=False)

	predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'),
							nullable=False)
