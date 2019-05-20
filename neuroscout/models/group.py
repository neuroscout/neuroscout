from sqlalchemy import (Column, Integer, ForeignKey, Text, String)
from sqlalchemy.orm import relationship

from .base import Base


class GroupPredictor(Base):
    """ Group-level predictors, e.g. across subjects, sessions, etc... """
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)  # Where to get this from?
    level = Column(String, nullable=False)  # Session? Subject?

    dataset_id = Column(
        Integer, ForeignKey('dataset.id'), nullable=False)

    values = relationship('GroupPredictorValue', backref='group_predictor')

    def __repr__(self):
        return '<models.GroupPredictor[name=%s]>' % self.name


class GroupPredictorValue(Base):
    """ Contains values of GroupPredictor for every Run.
        Also an association table between these two tables. """
    gp_id = Column(Integer, ForeignKey('group_predictor.id'),
                   primary_key=True)
    run_id = Column(Integer, ForeignKey('run.id'), primary_key=True)
    level_id = Column(String, primary_key=True)
    value = Column(String, nullable=False)
