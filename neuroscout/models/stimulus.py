from database import db

class Stimulus(db.Model):
	""" A unique stimulus. A stimulus may occur at different points in time,
		and perhaps even across different datasets. """
	id = db.Column(db.Integer, primary_key=True)
	sha1_hash = db.Column(db.Text, nullable=False, unique=True)
	mimetype = db.Column(db.Text, nullable=False)
	path = db.Column(db.Text, nullable=False)

	active = db.Column(db.Boolean, nullable=False, default=True)

	# For converted stimuli
	parent_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
	converter_name = db.Column(db.String)
	converter_parameters = db.Column(db.Text)

	extracted_events = db.relationship('ExtractedEvent', backref='stimulus',
	                            lazy='dynamic')
	runs = db.relationship('Run',
	                        secondary='run_stimulus',
	                        backref='stimulus')

	def __repr__(self):
	    return '<models.Stimulus[hash={}]>'.format(self.sha1_hash)


class RunStimulus(db.Model):
	""" Run Stimulus association table """
	stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'), primary_key=True)
	run_id = db.Column(db.Integer, db.ForeignKey('run.id'), primary_key=True)
	onset = db.Column(db.Float)
	duration = db.Column(db.Float)
