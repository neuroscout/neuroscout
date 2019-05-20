import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (Column, Integer, ForeignKey, Text,
                        Boolean, DateTime, String, Float)
from sqlalchemy.orm import relationship

from base import Base


class ExtractedFeature(Base):
    """ Events extracted from a Stimulus using an Extractor"""
    id = Column(Integer, primary_key=True)
    # Hash of next three variables
    sha1_hash = Column(Text, nullable=False)
    extractor_name = Column(String)
    extractor_parameters = Column(JSONB)
    feature_name = Column(String)
    original_name = Column(String)  # Original feature_name
    description = Column(String)
    active = Column(Boolean)
    modality = Column(String)
    transformed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    extractor_version = Column(Float, default=0.1)

    extracted_events = relationship(
        'ExtractedEvent', backref='extracted_feature')
    generated_predictors = relationship(
        'Predictor', backref='extracted_feature')

    def __repr__(self):
        return '<models.ExtractedFeature[feature_name=%s]>' % self.feature_name


class ExtractedEvent(Base):
    """ Events extracted from a Stimuli"""
    id = Column(Integer, primary_key=True)
    onset = Column(Float)
    duration = Column(Float)
    value = Column(String, nullable=False)
    history = Column(String)
    object_id = Column(Integer)

    stimulus_id = Column(
        Integer, ForeignKey('stimulus.id'), nullable=False)
    ef_id = Column(
        Integer, ForeignKey(ExtractedFeature.id), nullable=False)
