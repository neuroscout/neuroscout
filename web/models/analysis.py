from database import db
from db_utils import copy_row
from sqlalchemy.dialects.postgresql import JSONB
import datetime

from sqlalchemy.event import listens_for
from hashids import Hashids
from flask import current_app

# Association table between analysis and predictor.
analysis_predictor = db.Table('analysis_predictor',
                       db.Column('analysis_id', db.Integer(), db.ForeignKey('analysis.id')),
                       db.Column('predictor_id', db.Integer(), db.ForeignKey('predictor.id')))


class Analysis(db.Model):
    """" A single fMRI analysis. """
    id = db.Column(db.Integer, primary_key=True)
    hash_id = db.Column(db.Text, unique=True)

    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    data = db.Column(JSONB)
    filters = db.Column(JSONB) # List of filters used to select runs
    transformations = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_at = db.Column(db.DateTime)
    saved_count = db.Column(db.Integer)
    status = db.Column(db.Text)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # If cloned, this is the parent analysis:
    parent_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

    results = db.relationship('Result', backref='analysis',
                                lazy='dynamic')
    predictors = db.relationship('Predictor',
                                 secondary=analysis_predictor,
                                 backref='analysis')
    runs = db.relationship('Run',
                            secondary='analysis_run',
                            backref='analysis')

    def clone(self):
    	""" Make copy of analysis, with new id, and linking to parent """
    	clone_row = copy_row(Analysis, self, ignored_columns='analysis.id')
    	clone_row.parent = self.id
    	return clone_row

@listens_for(Analysis, "after_insert")
def update_hash(mapper, connection, target):
    analysis_table = mapper.local_table
    connection.execute(
          analysis_table.update().
              values(hash_id=Hashids(current_app.config['HASH_SALT']).encode(target.id)).
              where(analysis_table.c.id==target.id)
    )
