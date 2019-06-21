from ..database import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from .stimulus import Stimulus


class Dataset(db.Model):
    """ A BIDS dataset """
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(JSONB)  # BIDS description
    summary = db.Column(db.Text)  # Hand crafted summary
    url = db.Column(db.Text)  # External resource / link
    active = db.Column(db.Boolean, default=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    runs = db.relationship('Run', backref='dataset')
    predictors = db.relationship('Predictor', backref='dataset',
                                 lazy='dynamic')
    tasks = db.relationship('Task', backref='dataset')
    analyses = db.relationship('Analysis', backref='dataset')
    dataset_address = db.Column(db.Text)
    preproc_address = db.Column(db.Text)
    local_path = db.Column(db.Text)

    @hybrid_property
    def mimetypes(self):
        """ List of mimetypes of stimuli in dataset """
        return [s[0] for s in Stimulus.query.filter_by(
            dataset_id=self.id).distinct('mimetype').values('mimetype')]

    # Meta-data, such as preprocessed history, etc...
    def __repr__(self):
        return '<models.Dataset[name=%s]>' % self.name
