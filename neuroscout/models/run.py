from database import db

# Association table between analysis and run.
analysis_run = db.Table(
    'analysis_run',
    db.Column('analysis_id', db.Integer(), db.ForeignKey('analysis.id')),
    db.Column('run_id', db.Integer(), db.ForeignKey('run.id')))


class Run(db.Model):
    """ A single scan run. The basic unit of fMRI analysis. """
    __table_args__ = (
        db.UniqueConstraint(
            'session', 'subject', 'number', 'task_id', 'dataset_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    session = db.Column(db.Text)
    acquisition = db.Column(db.Text)

    subject = db.Column(db.Text)
    number = db.Column(db.Integer)

    duration = db.Column(db.Float)

    task_id = db.Column(db.Integer, db.ForeignKey('task.id'),
                        nullable=False)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey('dataset.id'), nullable=False)

    prs = db.relationship('PredictorRun',
                          cascade='delete')
    gpv = db.relationship('GroupPredictorValue',
                          cascade='delete')
    predictor_events = db.relationship(
        'PredictorEvent', backref='run',
        cascade='delete',
        lazy='dynamic')
    analyses = db.relationship(
        'Analysis', secondary='analysis_run')

    def __repr__(self):
        return '<models.Run[task={} sub={} sess={} number={}]>'.format(
            self.task, self.subject, self.session, self.number)
