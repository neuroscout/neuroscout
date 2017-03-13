from database import db

class ExtractedFeature(db.Model):
	""" Events extracted from a Stimuli using an Extractor"""
	id = db.Column(db.Integer, primary_key=True)
	description = db.Column(db.Text)

	extractor_id = db.Column(db.Integer, db.ForeignKey('extractor.id'))

	predictor_events = db.relationship('ExtractedEvent', backref='extractedfeature',
								lazy='dynamic')

class ExtractedEvent(db.Model):
	""" Events extracted from a Stimuli"""
	id = db.Column(db.Integer, primary_key=True)
	onset = db.Column(db.Float, nullable=False)
	duration = db.Column(db.Float)
	value = db.Column(db.Float, nullable=False)

	stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
	extracted_feature_id = db.Column(db.Integer, db.ForeignKey('extractedfeature.id'))
