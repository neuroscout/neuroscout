from flask import current_app

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.event import listens_for

from database import db
from utils.db import copy_row

from hashids import Hashids
import datetime

# Association table between analysis and predictor.
analysis_predictor = db.Table('analysis_predictor',
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

    model = db.Column(JSONB, default={}) # BIDS Model
    data = db.Column(JSONB, default={}) # Additional data (e.g. )
    filters = db.Column(JSONB) # List of filters used to select runs

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    compiled_at = db.Column(db.DateTime)
    saved_count = db.Column(db.Integer, default=0)

    status = db.Column(db.Text, default='DRAFT')
    __table_args__ = (
    	db.CheckConstraint(status.in_(['PASSED', 'FAILED', 'PENDING', 'DRAFT'])), )

    celery_error = db.Column(db.Text)
    celery_id = db.Column(db.Text) # Celery task id
    bundle_path = db.Column(db.Text)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'),
                           nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # If cloned, this is the parent analysis:
    parent_id = db.Column(db.Text, db.ForeignKey('analysis.hash_id'))

    results = db.relationship('Result', backref='analysis', lazy='dynamic')
    predictors = db.relationship('Predictor', secondary=analysis_predictor,
                                 backref='analysis')
    runs = db.relationship('Run', secondary='analysis_run')

    @hybrid_property
    def task_name(self):
        return self.runs[0].task.name if self.runs else None

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
        ## Copy relationships
        return clone_row

    def __repr__(self):
        return '<models.Analysis[hash_id=%s]>' % self.hash_id

@listens_for(Analysis, "after_insert")
def update_hash(mapper, connection, target):
    analysis_table = mapper.local_table
    connection.execute(
          analysis_table.update().
              values(hash_id=Hashids(current_app.config['HASH_SALT']).encode(target.id)).
              where(analysis_table.c.id==target.id)
    )
