from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import (Column, Integer, Text, Boolean)
from sqlalchemy.orm import relationship

from .base import Base
from .stimulus import Stimulus


class Dataset(Base):
    """ A BIDS dataset """
    id = Column(Integer, primary_key=True)
    description = Column(JSONB)  # BIDS description
    summary = Column(Text)  # Hand crafted summary
    url = Column(Text)  # External resource / link
    active = Column(Boolean, default=True)
    name = Column(Text, unique=True, nullable=False)
    runs = relationship('Run', backref='dataset')
    predictors = relationship('Predictor', backref='dataset',
                              lazy='dynamic')
    tasks = relationship('Task', backref='dataset')
    analyses = relationship('Analysis', backref='dataset')
    dataset_address = Column(Text)
    preproc_address = Column(Text)
    local_path = Column(Text)

    @hybrid_property
    def mimetypes(self):
        """ List of mimetypes of stimuli in dataset """
        return [s[0] for s in Stimulus.query.filter_by(
            dataset_id=self.id).distinct('mimetype').values('mimetype')]

    # Meta-data, such as preprocessed history, etc...

    def __repr__(self):
        return '<models.Dataset[name=%s]>' % self.name
