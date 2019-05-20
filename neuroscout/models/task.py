from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import (Column, Integer, ForeignKey, Text, Float,
                        UniqueConstraint)
from sqlalchemy.orm import relationship

from base import Base


class Task(Base):
    """ A task in a dataset. Usually associated with various runs. """
    __table_args__ = (
        UniqueConstraint('dataset_id', 'name'),
    )
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)  # Default: base path
    description = Column(JSONB)  # BIDS task description

    dataset_id = Column(Integer, ForeignKey('dataset.id'),
                        nullable=False)

    runs = relationship('Run', backref='task', cascade="delete")
    TR = Column(Float)
    summary = Column(Text)  # Summary annotation

    @hybrid_property
    def num_runs(self):
        """ List of mimetypes of stimuli in dataset """
        return len(self.runs)

    def __repr__(self):
        return '<models.Task[name={}]>'.format(self.name)
