from database import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from .run import Run
from .stimulus import Stimulus

class Dataset(db.Model):
	""" A BIDS dataset """
	id = db.Column(db.Text, primary_key=True)
	description = db.Column(JSONB) # BIDS description

	runs = db.relationship('Run', backref='dataset',
	                        lazy='dynamic')
	predictors = db.relationship('Predictor', backref='dataset',
	                             lazy='dynamic')

	@hybrid_property
	def mimetypes(self):
		""" List of mimetypes of stimuli in dataset """
		return [s.mimetype
				for r, s in db.session.query(
					Run, Stimulus).filter_by(
						dataset_id=self.id).distinct('mimetype')]

	@hybrid_property
	def tasks(self):
		""" List of tasks dataset """
		return [r.task for r in self.runs.distinct('task')]


	# Meta-data, such as preprocessed history, etc...
