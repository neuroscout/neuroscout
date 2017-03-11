from database import db

class Predictor(db.Model):
	""" Specific instantiation of a variable in a run, or a "column".

		A collection of PredictorEvents.

		In the case of ExtractedVariables, various can becombined
		to form a single predictor.

		In the case of OriginalVariable, it is usually a single variable per
		predictor.

	 	Also, join table between Analysis and Run. """
	id = db.Column(db.Integer, primary_key=True)

	run_id = db.Column(db.Integer, db.ForeignKey('run.id'))
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

	predictor_events = db.relationship('PredictorEvent', backref='predictor',
								lazy='dynamic')

class PredictorEvent(db.Model):
	""" A variable instantiated in a specifc run. Onset is relative to run. """
	id = db.Column(db.Integer, primary_key=True)
	onset = db.Column(db.Float, nullable=False)

	predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'))
	variable_id = db.Column(db.Integer, db.ForeignKey('variable.id'))
