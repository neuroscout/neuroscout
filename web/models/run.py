from database import db

class Run(db.Model):
	""" A single scan run. The basic unit of fMRI analysis. """
	id = db.Column(db.Integer, primary_key=True)
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))

	predictors = db.relationship('Predictor', backref='run',
                                lazy='dynamic')
