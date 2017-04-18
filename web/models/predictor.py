from database import db

class Predictor(db.Model):
	""" Instantiation of a predictor in a dataset.

		A collection of PredictorEvents.

	 	Also, joins Analysis and Run. """
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text, nullable=False)
	description = db.Column(db.Text)

	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
	ef_id = db.Column(db.Integer, db.ForeignKey('extractedfeature.id'))

	predictor_events = db.relationship('PredictorEvent', backref='predictor',
								lazy='dynamic')

class PredictorRun(db.Model):
    """ Predictor Run association table """
    predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'), primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), primary_key=True)
	# Cache a plot of the timecourse
	# Run level Predictor diagnostics (cached) will go in here

class PredictorEvent(db.Model):
	""" An event within a Predictor. Onset is relative to run. """
	__table_args__ = (
	    db.UniqueConstraint('onset', 'run_id'),
	)
	id = db.Column(db.Integer, primary_key=True)

	onset = db.Column(db.Float, nullable=False)
	duration = db.Column(db.Float)
	value = db.Column(db.String, nullable=False)

	run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)

	predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'),
							nullable=False)
