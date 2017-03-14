from database import db

class Stimulus(db.Model):
	""" A unique stimulus. A stimulus may occur at different points in time,
		and perhaps even across different datasets"""
	id = db.Column(db.Integer, primary_key=True)

	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))

	extracted_events = db.relationship('ExtractedEvent', backref='stimulus',
                                lazy='dynamic')

class RunStimulus(db.Model):
    """ Run Stimulus association table """
    stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'), primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), primary_key=True)
    onset = db.Column(db.Float, nullable=False)
