from database import db

class Stimulus(db.Model):
	""" Points to unique stimulus """
	id = db.Column(db.Integer, primary_key=True)
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	predictors = db.relationship('Predictor', backref='stimulus',
                                lazy='dynamic')

	## Hash of actual file. MD5 has of the unique file

### Many to many between analysis and predictor
# Many to many:
# class App(db.Model):
# 	id = db.Column(db.Integer, primary_key=True) 