from database import db
from sqlalchemy.dialects.postgresql import JSON

class Dataset(db.Model):
	""" A BIDS dataset """
	id = db.Column(db.Integer, primary_key=True)
	description = db.Column(JSON) ## BIDS specification
	name = db.Column(db.String(30), nullable=False)
	external_id = db.Column(db.String(30), unique=True, nullable=False)

	analyses = db.relationship('Analysis', backref='dataset',
                                lazy='dynamic')
	runs = db.relationship('Runs', backref='dataset',
                                lazy='dynamic')
