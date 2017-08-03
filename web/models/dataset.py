from database import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from .run import Run
from .stimulus import Stimulus

class Dataset(db.Model):
	""" A BIDS dataset """
	id = db.Column(db.Integer, primary_key=True)
	description = db.Column(JSONB) # BIDS description
	name = db.Column(db.Text, unique=True, nullable=False)
	runs = db.relationship('Run', backref='dataset',
	                        lazy='dynamic')
	predictors = db.relationship('Predictor', backref='dataset',
	                             lazy='dynamic')

	tasks = db.relationship('Task', backref='dataset')
	analyses = db.relationship('Analysis', backref='dataset',
	                            lazy='dynamic')
	address = db.Column(db.Text)
	
	@hybrid_property
	def mimetypes(self):
		""" List of mimetypes of stimuli in dataset """
		return [s.mimetype
				for r, s in db.session.query(
					Run, Stimulus).filter_by(
						dataset_id=self.id).distinct('mimetype')]

	# Meta-data, such as preprocessed history, etc...
