from database import db

# Association table between analysis and run.
analysis_run = db.Table('analysis_run',
                       db.Column('analysis_id', db.Integer(), db.ForeignKey('analysis.id')),
                       db.Column('run_id', db.Integer(), db.ForeignKey('run.id')))

class Run(db.Model):
	""" A single scan run. The basic unit of fMRI analysis. """
	id = db.Column(db.Integer, primary_key=True)
	session = db.Column(db.Text)
	subject = db.Column(db.Text)
	number = db.Column(db.Text)
	task = db.Column(db.Text)

	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))

	predictors = db.relationship('Predictor', backref='run',
                                lazy='dynamic')
