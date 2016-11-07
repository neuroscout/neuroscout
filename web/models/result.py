from database import db

class Result(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))