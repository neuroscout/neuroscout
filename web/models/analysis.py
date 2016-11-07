from database import db

class Analysis(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	results = db.relationship('Result', backref='analysis',
                                lazy='dynamic')
	name = db.Column(db.String(30))
	description = db.Column(db.String(30))
	timelines = db.relationship('Timeline', backref='analysis',
                                lazy='dynamic')
	parent = db.Column(db.String(30))
