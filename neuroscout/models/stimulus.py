from database import db


class Stimulus(db.Model):
    """ A unique stimulus. A stimulus may occur at different points in time,
        and perhaps even across different datasets. """
    __table_args__ = (
        db.UniqueConstraint('sha1_hash', 'dataset_id', 'converter_name',
                            'parent_id'),
    )

    __table_args__ = (
          db.CheckConstraint('NOT(path IS NULL AND content IS NULL)'),
    )

    id = db.Column(db.Integer, primary_key=True)
    sha1_hash = db.Column(db.Text, nullable=False)
    mimetype = db.Column(db.Text, nullable=False)

    path = db.Column(db.Text)
    content = db.Column(db.Text)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'),
                           nullable=False)

    active = db.Column(db.Boolean, nullable=False, default=True)

    # For converted stimuli
    parent_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
    converter_name = db.Column(db.String)
    converter_parameters = db.Column(db.Text)

    extracted_events = db.relationship('ExtractedEvent')
    runs = db.relationship('Run', secondary='run_stimulus')
    run_stimuli = db.relationship('RunStimulus', backref='stimulus')

    def __repr__(self):
        return '<models.Stimulus[hash={}]>'.format(self.sha1_hash)


class RunStimulus(db.Model):
    """ Run Stimulus association table """
    __table_args__ = (
        db.UniqueConstraint('stimulus_id', 'run_id', 'onset'),
    )
    id = db.Column(db.Integer, primary_key=True)
    stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'))
    onset = db.Column(db.Float)
    duration = db.Column(db.Float)
