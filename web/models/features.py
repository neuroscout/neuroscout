from database import db

class ExtractedFeature(db.Model):
	""" Events extracted from a Stimulus using an Extractor"""
	id = db.Column(db.Integer, primary_key=True)
	sha1_hash = db.Column(db.Text, nullable=False, unique=True)

	extractor_name = db.Column(db.String)
	feature_name = db.Column(db.String)

	# extractor_id = db.Column(db.Integer, db.ForeignKey('extractor.id'))

	extracted_events = db.relationship('ExtractedEvent', backref='extractedfeature',
                                lazy='dynamic')


class ExtractedEvent(db.Model):
	""" Events extracted from a Stimuli"""
	id = db.Column(db.Integer, primary_key=True)
	onset = db.Column(db.Float)
	duration = db.Column(db.Float)
	value = db.Column(db.Float, nullable=False)
	history = db.Column(db.String)

	stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'), nullable=False)
	ef_id = db.Column(db.Integer, db.ForeignKey(ExtractedFeature.id),
						   nullable=False)
