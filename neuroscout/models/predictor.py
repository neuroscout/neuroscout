from sqlalchemy import (Column, Integer, ForeignKey, Text, String,
                        Boolean, Float, UniqueConstraint, Index)
from sqlalchemy.orm import relationship

from .base import Base


class Predictor(Base):
    """ Instantiation of a predictor in a dataset.
    A collection of PredictorEvents. """

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    original_name = Column(Text)
    source = Column(Text)
    description = Column(Text)

    dataset_id = Column(Integer, ForeignKey('dataset.id'),
                        nullable=False)
    ef_id = Column(Integer, ForeignKey('extracted_feature.id'))

    predictor_events = relationship('PredictorEvent', backref='predictor')

    predictor_run = relationship('PredictorRun')
    active = Column(Boolean, default=True)  # Actively display or not

    def __repr__(self):
        return '<models.Predictor[name=%s]>' % self.name


class PredictorEvent(Base):
    """ An event within a Predictor. Onset is relative to run. """
    __table_args__ = (
        UniqueConstraint('onset', 'run_id', 'predictor_id', 'object_id'),
        Index('ix_predictor_id_run_id', "predictor_id", "run_id")
    )
    id = Column(Integer, primary_key=True)

    onset = Column(Float, nullable=False)
    duration = Column(Float)
    value = Column(String, nullable=False)
    object_id = Column(Integer)

    run_id = Column(Integer, ForeignKey('run.id'), nullable=False,
                    index=True)
    predictor_id = Column(Integer, ForeignKey('predictor.id'),
                          nullable=False, index=True)
    stimulus_id = Column(Integer, ForeignKey('stimulus.id'))

    def __repr__(self):
        return '<models.PredictorEvent[run_id={} predictor={}]>'.format(
            self.run_id, self.predictor.name)


class PredictorRun(Base):
    """ Predictor run association cache table """
    run_id = Column(Integer, ForeignKey('run.id'), primary_key=True)
    predictor_id = Column(Integer, ForeignKey('predictor.id'),
                          primary_key=True)
