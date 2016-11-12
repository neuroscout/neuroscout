from database import db
from db_utils import copy_row

class Analysis(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	results = db.relationship('Result', backref='analysis',
                                lazy='dynamic')
	name = db.Column(db.String(30), nullable=False)
	description = db.Column(db.String(30))
	predictors = db.relationship('Predictor', backref='analysis',
                                lazy='dynamic')
	parent_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

	def clone(self):
		""" Make copy of analysis, with new id, and linking to parent """
		clone_row = copy_row(Analysis, self, ignored_columns='analysis.id')
		clone_row.parent = self.id
		return clone_row