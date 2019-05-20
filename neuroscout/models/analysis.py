import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import (Column, Integer, Table, ForeignKey, Text,
                        Boolean, DateTime, CheckConstraint)
from sqlalchemy.orm import relationship

from .base import Base
from .utils import copy_row

# Association table between analysis and predictor.
analysis_predictor = Table(
    'analysis_predictor',
    Base.metadata,
    Column('analysis_id', Integer(), ForeignKey('analysis.id')),
    Column('predictor_id', Integer(), ForeignKey('predictor.id')))


class Analysis(Base):
    """" A single fMRI analysis. """
    id = Column(Integer, primary_key=True)
    hash_id = Column(Text, unique=True)

    name = Column(Text, nullable=False)
    description = Column(Text)
    predictions = Column(Text, default='')
    private = Column(Boolean, default=True)

    model = Column(JSONB, default={})  # BIDS Model
    data = Column(JSONB, default={})  # Additional data (e.g. )
    filters = Column(JSONB)  # List of filters used to select runs

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)
    submitted_at = Column(DateTime)
    saved_count = Column(Integer, default=0)

    status = Column(Text, default='DRAFT')
    __table_args__ = (
        CheckConstraint(
            status.in_(
                ['PASSED', 'FAILED', 'SUBMITTING', 'PENDING', 'DRAFT'])), )

    locked = Column(Boolean, default=False)

    compile_traceback = Column(Text, default='')
    compile_task_id = Column(Text)  # Celery task id
    bundle_path = Column(Text)

    dataset_id = Column(Integer, ForeignKey('dataset.id'),
                        nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    # If cloned, this is the parent analysis:
    parent_id = Column(Text, ForeignKey('analysis.hash_id'))

    predictors = relationship('Predictor', secondary=analysis_predictor,
                              backref='analysis')
    runs = relationship('Run', secondary='analysis_run')

    @hybrid_property
    def task_name(self):
        return self.runs[0].task.name if self.runs else None

    @hybrid_property
    def subject(self):
        items = list(set([run.subject for run in self.runs]) - set([None]))
        if len(items) == 0:
            items = None
        return items

    @hybrid_property
    def run(self):
        items = list(set([int(run.number)
                          for run in self.runs
                          if run.number is not None]) - set([None]))
        if len(items) == 0:
            items = None
        return items

    @hybrid_property
    def session(self):
        items = list(set([run.session for run in self.runs]) - set([None]))
        if len(items) == 0:
            items = None
        return items

    @hybrid_property
    def TR(self):
        return self.runs[0].task.TR if self.runs else None

    def clone(self, user):
        """ Make copy of analysis, with new id, and linking to parent """
        clone_row = copy_row(Analysis, self,
                             ignored_columns=['id', 'hash_id'])
        clone_row.parent_id = self.hash_id
        clone_row.user_id = user.id
        clone_row.status = "DRAFT"
        # Copy relationships
        return clone_row

    def __repr__(self):
        return '<models.Analysis[hash_id =%s]>' % self.hash_id


class Report(Base):
    """" Report generation table"""
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Text, ForeignKey('analysis.hash_id'))
    runs = Column(JSONB, default=None)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    task_id = Column(Text)   # Celery task id
    result = Column(JSONB)  # JSON result from Celery (once finished)
    traceback = Column(Text)

    status = Column(Text, default='PENDING')
    __table_args__ = (
        CheckConstraint(status.in_(['OK', 'FAILED', 'PENDING'])), )


class NeurovaultCollection(Base):
    """ Neurovault collection and upload status """
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Text, ForeignKey('analysis.hash_id'))
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    task_id = Column(Text)
    collection_id = Column(Text)
    traceback = Column(Text)

    status = Column(Text, default='PENDING')
    __table_args__ = (
        CheckConstraint(status.in_(['OK', 'FAILED', 'PENDING'])), )
