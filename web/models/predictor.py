from database import db

class Predictor(db.Model):
	""" Instantiation of a predictor in a dataset.
		A collection of PredictorEvents. """
	__table_args__ = (
		db.UniqueConstraint('name', 'dataset_id'),
	)
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text, nullable=False)
	description = db.Column(db.Text) # Where to get this from?

	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
	ef_id = db.Column(db.Integer, db.ForeignKey('extracted_feature.id'))

	predictor_events = db.relationship('PredictorEvent', backref='predictor',
								lazy='dynamic')


class PredictorEvent(db.Model):
	""" An event within a Predictor. Onset is relative to run. """
	__table_args__ = (
	    db.UniqueConstraint('onset', 'run_id', 'predictor_id'),
	)
	id = db.Column(db.Integer, primary_key=True)

	onset = db.Column(db.Float, nullable=False)
	duration = db.Column(db.Float)
	value = db.Column(db.String, nullable=False)

	run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)
	predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'),
							nullable=False)

# class PredictorDataset(db.Model):
#     """ Predictor dataset association table """
#     predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'), primary_key=True)
#     run_id = db.Column(db.Integer, db.ForeignKey('run.id'), primary_key=True)
# 	# Cache a plot of the timecourse
# 	# Run level Predictor diagnostics (cached) will go in here

# PredictorRun table does not make sense since Run is tied to PredictorEvent now
# Separate cache table?
