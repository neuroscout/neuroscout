from database import db

class Stimulus(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	## Onset and duration?
	predictors = db.relationship('Predictor', backref='stimulus',
                                lazy='dynamic')


### Many to many between analysis and predictor
# Many to many:
# class App(db.Model):
# 	id = db.Column(db.Integer, primary_key=True) 