from database import db
from sqlalchemy.dialects.postgresql import JSON

class Dataset(db.Model):
	""" A BIDS dataset """
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text, nullable=False, unique=True)

	description = db.Column(JSON) # BIDS description
	task_description = db.Column(JSON) # BIDS task descrition
	task = db.Column(db.Text, nullable=False)
	analyses = db.relationship('Analysis', backref='dataset',
                                lazy='dynamic')
	runs = db.relationship('Run', backref='dataset',
                                lazy='dynamic')
