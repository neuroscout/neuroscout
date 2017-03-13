from database import db

class Extractor(db.Model):
	""" A pliers extractor that transforms a Stimulus into ExtractedEvents """
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String
	description = db.Column(db.Text)
	version = db.Column(db.Float)
	input_type = db.Column(db.Text)
	output_type  = db.Column(db.Text)

	extracted_features = db.relationship('ExtractedFeature', backref='extractor',
                                lazy='dynamic')
