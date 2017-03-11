from database import db

class Variable(db.Model):
	""" A set of Events. """
	id = db.Column(db.Integer, primary_key=True)
	events = db.relationship('VariableEvent', backref='variable',
                                lazy='dynamic')
	predictor_var = db.relationship('PredictorEvent', backref='variable',
								lazy='dynamic')
class ExtractedVariable(Variable):
	""" A variable extracted from a Stimulus using an Extractor. """
	id = db.Column(db.Integer, db.ForeignKey('variable.id'), primary_key=True)
	extractor_id = db.Column(db.Integer, db.ForeignKey('extractor.id'))
	stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))

class OriginalVariable(Variable):
	""" A variable that appears in the original BIDS study (e.g. RT) """
	id = db.Column(db.Integer, db.ForeignKey('variable.id'), primary_key=True)


class VariableEvent(db.Model):
	"""" Events that compose a variable.
	Onsets are relative (i.e. not absolute onsets in runs)"""
	id = db.Column(db.Integer, primary_key=True)
	onset = db.Column(db.Float, nullable=False)
	duration = db.Column(db.Float, nullable=False)
	value = db.Column(db.Float, nullable=False)

	variable_id = db.Column(db.Integer, db.ForeignKey('variable.id'))
