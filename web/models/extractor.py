from database import db

class Extractor(db.Model):
	""" A pliers extractor that transforms a Stimulus into a Variable """
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30))
	description = db.Column(db.String(30))
	version = db.Column(db.Float(10))
	input_type = db.Column(db.String(20))
	output_type  = db.Column(db.String(20))

	extracted_variables = db.relationship('ExtractedVariable', backref='extractor',
                                lazy='dynamic')
