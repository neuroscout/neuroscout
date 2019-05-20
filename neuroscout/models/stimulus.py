from sqlalchemy import (Column, Integer, ForeignKey, Text, String, Float,
                        Boolean, CheckConstraint, UniqueConstraint)
from sqlalchemy.orm import relationship

from base import Base


class Stimulus(Base):
    """ A unique stimulus. A stimulus may occur at different points in time,
        and perhaps even across different datasets. """
    __table_args__ = (
        UniqueConstraint('sha1_hash', 'dataset_id', 'converter_name',
                         'parent_id'),
    )

    __table_args__ = (
          CheckConstraint('NOT(path IS NULL AND content IS NULL)'),
    )

    id = Column(Integer, primary_key=True)
    sha1_hash = Column(Text, nullable=False)
    mimetype = Column(Text, nullable=False)

    path = Column(Text)
    content = Column(Text)

    dataset_id = Column(Integer, ForeignKey('dataset.id'),
                        nullable=False)

    active = Column(Boolean, nullable=False, default=True)

    # For converted stimuli
    parent_id = Column(Integer, ForeignKey('stimulus.id'))
    converter_name = Column(String)
    converter_parameters = Column(Text)

    extracted_events = relationship('ExtractedEvent')
    runs = relationship('Run', secondary='run_stimulus')
    run_stimuli = relationship('RunStimulus', backref='stimulus',
                               lazy='dynamic')

    def __repr__(self):
        return '<models.Stimulus[hash={}]>'.format(self.sha1_hash)


class RunStimulus(Base):
    """ Run Stimulus association table """
    __table_args__ = (
        UniqueConstraint('stimulus_id', 'run_id', 'onset'),
    )
    id = Column(Integer, primary_key=True)
    stimulus_id = Column(Integer, ForeignKey('stimulus.id'))
    run_id = Column(Integer, ForeignKey('run.id'))
    onset = Column(Float)
    duration = Column(Float)
