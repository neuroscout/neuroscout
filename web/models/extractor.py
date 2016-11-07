from database import db

class Extractor(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30))
	timelines = db.relationship('Timeline', backref='extractor',
                                lazy='dynamic')
	description = db.Column(db.String(30))
	version = db.Column(db.Float(10))
	input_type = db.Column(db.String(20))
	output_type  = db.Column(db.String(20))