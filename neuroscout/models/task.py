from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
import statistics
from sqlalchemy import func
from .run import Run
from ..database import db


class Task(db.Model):
    """ A task in a dataset. Usually associated with various runs. """
    __table_args__ = (
        db.UniqueConstraint('dataset_id', 'name'),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)  # Default: base path
    description = db.Column(JSONB)  # BIDS task description

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'),
                           nullable=False)

    runs = db.relationship('Run', backref='task', cascade="delete")
    TR = db.Column(db.Float)
    summary = db.Column(db.Text)  # Summary annotation

    @hybrid_property
    def n_subjects(self):
        """ Number of subjects in task """
        return Run.query.filter_by(
            task_id=self.id).distinct('subject').count()

    @hybrid_property
    def n_runs_subject(self):
        """ Number of runs per subject """
        runs = [r[1] for r in db.session.query(
            Run.subject, func.count(Run.id)).filter_by(
                task_id=self.id).group_by(Run.subject)]
        return statistics.mean(runs) if runs else 0
            
    @hybrid_property
    def avg_run_duration(self):
        """ Average run duration (seconds) """
        avg_run = db.session.query(func.avg(Run.duration)).filter_by(
            task_id=self.id).all()[0][0]
        if avg_run:
            avg_run = round(avg_run, 2)
        return avg_run

    def __repr__(self):
        return '<models.Task[name={}]>'.format(self.name)
