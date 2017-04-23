from database import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from .run import Run
from .stimulus import Stimulus
from sqlalchemy import select

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
		return [s.mimetype
				for r, s in db.session.query(
					Run, Stimulus).filter_by(
						dataset_id=self.id).distinct('mimetype')]

	@mimetypes.expression
	def mimetypes(cls):
		return select([Stimulus.mimetype]).select_from(
			Stimulus.join(Run)).where(Run.dataset_id == cls.id).distinct()

	# Meta-data, such as preprocessed history, etc...
	@hybrid_property
	def tasks(self):
	    return [r.task for r in self.runs.distinct('task')]

	@tasks.expression
	def tasks(cls):
	    return select([Run.task]).where(
			Run.dataset_id == cls.id).distinct()
