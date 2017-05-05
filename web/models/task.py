from database import db
from sqlalchemy.dialects.postgresql import JSONB

class Task(db.Model):
    """ A task in a dataset. Usually associated with various runs. """
    __table_args__ = (
        db.UniqueConstraint('dataset_id', 'name'),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False) # Default: base path
    description = db.Column(JSONB) # BIDS task description

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'),
                           nullable=False)

    runs = db.relationship('Run', backref='task')
