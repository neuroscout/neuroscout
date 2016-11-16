from database import db
from sqlalchemy.dialects.postgresql import JSON

class Dataset(db.Model):
	id = db.Column(db.Integer, primary_key=True)	
	analyses = db.relationship('Analysis', backref='dataset',
                                lazy='dynamic')
	stimuli = db.relationship('Stimulus', backref='dataset',
                                lazy='dynamic')
	description = db.Column(JSON) ## BIDS specification
	name = db.Column(db.String(30), nullable=False)
	external_id = db.Column(db.String(30), unique=True, nullable=False)


	## Should we also have a task model? Since ds can have multiple tasks
	## Should we represent details such as aquisition parameters, or leave to BIDS
		# - May want to show to users
		# It may make sense to have BIDS marshamllow to model deserializer
			# e.g. have a 1:1 match between description and acq params