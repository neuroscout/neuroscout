from ..app import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property

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

    runs = db.relationship('Run', backref='task', cascade="delete")
    TR = db.Column(db.Float)

    @hybrid_property
    def num_runs(self):
    	""" List of mimetypes of stimuli in dataset """
    	return len(self.runs)

    def __repr__(self):
        return '<models.Task[name={}]>'.format(self.name)
