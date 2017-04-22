from database import db
from sqlalchemy.dialects.postgresql import JSON

# Association table between analysis and run.
analysis_run = db.Table('analysis_run',
                       db.Column('analysis_id', db.Integer(), db.ForeignKey('analysis.id')),
                       db.Column('run_id', db.Integer(), db.ForeignKey('run.id')))

class Run(db.Model):
    """ A single scan run. The basic unit of fMRI analysis. """
    __table_args__ = (
        db.UniqueConstraint('session', 'subject', 'number', 'task', 'dataset_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    session = db.Column(db.Text)
    subject = db.Column(db.Text)
    number = db.Column(db.Text)
    task = db.Column(db.Text)

    duration = db.Column(db.Float)
    task_description = db.Column(JSON) # BIDS task description
    TR = db.Column(db.Float)
    path = db.Column(db.Text) # Relative to BIDS root

    dataset_id = db.Column(db.Text, db.ForeignKey('dataset.id'), nullable=False)
    predictor_events = db.relationship('PredictorEvent', backref='run',
                                        lazy='dynamic')
    analyses = db.relationship('Analysis',
                            secondary='analysis_run',
                            backref='run',
                            lazy='dynamic')
    stimuli = db.relationship('Stimulus',
                            secondary='run_stimulus',
                            backref='run',
                            lazy='dynamic')


    # Anything else that a nipype interface needs to work with that run?
