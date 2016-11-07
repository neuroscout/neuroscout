from database import db
from sqlalchemy.dialects.postgresql import JSON

class Dataset(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	analyses = db.relationship('Analysis', backref='dataset',
                                lazy='dynamic')
	stimuli = db.relationship('Stimulus', backref='dataset',
                                lazy='dynamic')
	attributes = db.Column(JSON) ## BIDS specification
	name = db.Column(db.String(30))
	external_id = db.Column(db.String(30), unique=True)
	events = db.Column(db.Text()) # TSV events file
