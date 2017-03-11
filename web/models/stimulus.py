from database import db

# Join table between stimuli and runs.
run_stimuli = db.Table('run_stimuli',
                       db.Column('run_id', db.Integer(), db.ForeignKey('run.id')),
                       db.Column('stimulus_id', db.Integer(), db.ForeignKey('stimulus.id')))


class Stimulus(db.Model):
	""" A unique stimulus. A stimulus may occur at different points in time,
		and perhaps even across different datasets"""
	id = db.Column(db.Integer, primary_key=True)

	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))

	variables = db.relationship('ExtractedVariable', backref='stimulus',
                                lazy='dynamic')
