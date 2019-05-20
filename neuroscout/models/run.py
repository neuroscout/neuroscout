from sqlalchemy import (Column, Integer, Table, ForeignKey, Text, Float,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from .base import Base


# Association table between analysis and run.
analysis_run = Table(
    'analysis_run',
    Column('analysis_id', Integer(), ForeignKey('analysis.id')),
    Column('run_id', Integer(), ForeignKey('run.id')))


class Run(Base):
    """ A single scan run. The basic unit of fMRI analysis. """
    __table_args__ = (
        UniqueConstraint(
            'session', 'subject', 'number', 'task_id', 'dataset_id'),
    )
    id = Column(Integer, primary_key=True)
    session = Column(Text)
    acquisition = Column(Text)

    subject = Column(Text)
    number = Column(Integer)

    duration = Column(Float)

    task_id = Column(Integer, ForeignKey('task.id'),
                     nullable=False)
    dataset_id = Column(
        Integer, ForeignKey('dataset.id'), nullable=False)

    prs = relationship('PredictorRun',
                       cascade='delete')
    gpv = relationship('GroupPredictorValue',
                       cascade='delete')
    predictor_events = relationship(
        'PredictorEvent', backref='run',
        cascade='delete',
        lazy='dynamic')
    analyses = relationship(
        'Analysis', secondary='analysis_run')

    def __repr__(self):
        return '<models.Run[task={} sub={} sess={} number={}]>'.format(
            self.task, self.subject, self.session, self.number)
