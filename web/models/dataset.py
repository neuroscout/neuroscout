from database import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.hybrid import hybrid_property

class Dataset(db.Model):
	""" A BIDS dataset """
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text, nullable=False, unique=True)

	description = db.Column(JSON) # BIDS description
	mimetypes =  db.Column(JSON) # Mimetypes in stimuli

	runs = db.relationship('Run', backref='dataset',
                            lazy='dynamic')
	predictors = db.relationship('Predictor', backref='dataset',
	                             lazy='dynamic')

	# Meta-data, such as preprocessed history, etc...
	@hybrid_property
	def tasks(self):
	    return [r.task for r in self.runs.distinct('task')]
