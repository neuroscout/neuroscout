from ..database import db
import datetime
from sqlalchemy.dialects.postgresql import JSONB


class ExtractedFeature(db.Model):
    """ Events extracted from a Stimulus using an Extractor"""
    id = db.Column(db.Integer, primary_key=True)
    # Hash of next three variables
    sha1_hash = db.Column(db.Text, nullable=False)
    extractor_name = db.Column(db.String)
    extractor_parameters = db.Column(JSONB)
    feature_name = db.Column(db.String)
    original_name = db.Column(db.String)  # Original feature_name
    description = db.Column(db.String)
    active = db.Column(db.Boolean)
    modality = db.Column(db.String)
    transformed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    extractor_version = db.Column(db.Float, default=0.1)

    extracted_events = db.relationship(
        'ExtractedEvent', backref='extracted_feature')
    generated_predictors = db.relationship(
        'Predictor', backref='extracted_feature')

    def __repr__(self):
        return '<models.ExtractedFeature[feature_name=%s]>' % self.feature_name


class ExtractedEvent(db.Model):
    """ Events extracted from a Stimuli"""
    id = db.Column(db.Integer, primary_key=True)
    onset = db.Column(db.Float)
    duration = db.Column(db.Float)
    value = db.Column(db.String, nullable=False)
    object_id = db.Column(db.Integer)

    stimulus_id = db.Column(
        db.Integer, db.ForeignKey('stimulus.id'), nullable=False)
    ef_id = db.Column(
        db.Integer, db.ForeignKey(ExtractedFeature.id), nullable=False)
