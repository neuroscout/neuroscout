from database import db

class Event(db.Model):
	"""" Extracted feature events. Onsets are relative to the stimulus, not
	subject """
	id = db.Column(db.Integer, primary_key=True) 
	onset = db.Column(db.Float, nullable=False) 
	duration = db.Column(db.Float, nullable=False) 
	amplitude = db.Column(db.Float, nullable=False) 

	predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'))
