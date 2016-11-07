from database import db

class Timeline(db.Model):
	id = db.Column(db.Integer, primary_key=True) 
	extractor_id = db.Column(db.Integer, db.ForeignKey('extractor.id'))
	analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
	stimuli_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
	event_file = db.Column(db.String)