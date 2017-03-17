from database import db
from db_utils import copy_row

# Association table between analysis and predictor.
analysis_predictor = db.Table('analysis_predictor',
                       db.Column('analysis_id', db.Integer(), db.ForeignKey('analysis.id')),
                       db.Column('predictor_id', db.Integer(), db.ForeignKey('predictor.id')))


class Analysis(db.Model):
	"""" A single fMRI analysis. """
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False)
	description = db.Column(db.Text)

	dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	# If cloned, this is the parent analysis:
	parent_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

	results = db.relationship('Result', backref='analysis',
                                lazy='dynamic')

	def clone(self):
		""" Make copy of analysis, with new id, and linking to parent """
		clone_row = copy_row(Analysis, self, ignored_columns='analysis.id')
		clone_row.parent = self.id
		return clone_row
