from ..app import db

class Result(db.Model):
	"""" Some representation of the result of an analysis. TBD """
	id = db.Column(db.Integer, primary_key=True)

	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
