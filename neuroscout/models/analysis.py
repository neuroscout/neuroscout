from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property

from ..database import db
from .utils import copy_row

import datetime

# Association table between analysis and predictor.
analysis_predictor = db.Table(
    'analysis_predictor',
    db.Column('analysis_id', db.Integer(), db.ForeignKey('analysis.id')),
    db.Column('predictor_id', db.Integer(), db.ForeignKey('predictor.id')))


class Analysis(db.Model):
    """" A single fMRI analysis. """
    id = db.Column(db.Integer, primary_key=True)
    hash_id = db.Column(db.Text, unique=True)

    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    predictions = db.Column(db.Text, default='')
    private = db.Column(db.Boolean, default=True)

    model = db.Column(JSONB, default={})  # BIDS Model
    data = db.Column(JSONB, default={})  # Additional data (e.g. )
    filters = db.Column(JSONB)  # List of filters used to select runs

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    saved_count = db.Column(db.Integer, default=0)

    status = db.Column(db.Text, default='DRAFT')
    __table_args__ = (
        db.CheckConstraint(
            status.in_(
                ['PASSED', 'FAILED', 'SUBMITTING', 'PENDING', 'DRAFT'])), )

    locked = db.Column(db.Boolean, default=False)

    traceback = db.Column(db.Text, default='')
    compile_task_id = db.Column(db.Text)  # Celery task id
    bundle_path = db.Column(db.Text)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'),
                           nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # If cloned, this is the parent analysis:
    parent_id = db.Column(db.Text, db.ForeignKey('analysis.hash_id'))

    predictors = db.relationship('Predictor', secondary=analysis_predictor,
                                 backref='analysis')
    runs = db.relationship('Run', secondary='analysis_run')

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


class Report(db.Model):
    """" Report generation table"""
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Text, db.ForeignKey('analysis.hash_id'))
    runs = db.Column(JSONB, default=None)
    generated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    task_id = db.Column(db.Text)   # Celery task id
    result = db.Column(JSONB)  # JSON result from Celery (once finished)
    traceback = db.Column(db.Text)

    status = db.Column(db.Text, default='PENDING')
    __table_args__ = (
        db.CheckConstraint(status.in_(['OK', 'FAILED', 'PENDING'])), )


class NeurovaultCollection(db.Model):
    """ Neurovault collection and upload status """
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Text, db.ForeignKey('analysis.hash_id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    collection_id = db.Column(db.Integer, unique=True)

    files = db.relationship('NeurovaultFileUpload', backref='collection')


class NeurovaultFileUpload(db.Model):
    """ NV file upload """
    id = db.Column(db.Integer, primary_key=True)
    nv_collection_id = db.Column(
        db.Integer, db.ForeignKey('neurovault_collection.id'),
        nullable=False)

    path = db.Column(db.Text, nullable=False)

    task_id = db.Column(db.Text)
    level = db.Column(db.Text, nullable=False)

    exception = db.Column(db.Text)
    traceback = db.Column(db.Text)

    status = db.Column(db.Text, default='PENDING')
    __table_args__ = (
        db.CheckConstraint(status.in_(['OK', 'FAILED', 'PENDING'])),
        db.CheckConstraint(level.in_(['GROUP', 'SUBJECT'])),
        )
