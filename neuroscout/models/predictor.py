from database import db
import statistics
from sqlalchemy import func, Numeric, cast


class Predictor(db.Model):
    """ Instantiation of a predictor in a dataset.
    A collection of PredictorEvents. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    original_name = db.Column(db.Text)
    source = db.Column(db.Text)
    description = db.Column(db.Text)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'),
                           nullable=False)
    ef_id = db.Column(db.Integer, db.ForeignKey('extracted_feature.id'))

    predictor_events = db.relationship('PredictorEvent', backref='predictor')

    run_statistics = db.relationship('PredictorRun')
    active = db.Column(db.Boolean, default=True)  # Actively display or not

    def __repr__(self):
        return '<models.Predictor[name=%s]>' % self.name


class PredictorEvent(db.Model):
    """ An event within a Predictor. Onset is relative to run. """
    __table_args__ = (
        db.UniqueConstraint('onset', 'run_id', 'predictor_id', 'object_id'),
        db.Index('ix_predictor_id_run_id', "predictor_id", "run_id")
    )
    id = db.Column(db.Integer, primary_key=True)

    onset = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float)
    value = db.Column(db.String, nullable=False)
    object_id = db.Column(db.Integer)

    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False,
                       index=True)
    predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'),
                             nullable=False, index=True)
    stimulus_id = db.Column(db.Integer, db.ForeignKey('stimulus.id'))

    def __repr__(self):
        return '<models.PredictorEvent[run_id={} predictor={}]>'.format(
            self.run_id, self.predictor.name)


class PredictorRun(db.Model):
    """ Predictor run association cache table """
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), primary_key=True)
    predictor_id = db.Column(db.Integer, db.ForeignKey('predictor.id'),
                             primary_key=True)

    def stat_property(function):
        @property
        def wrapper(self):
            val_query = PredictorEvent.query.filter_by(
                    run_id=self.run_id,
                    predictor_id=self.predictor_id).with_entities('value')
            try:
                return function(self, [float(a[0]) for a in val_query])
            except ValueError:
                return None
        return wrapper

    @stat_property
    def mean(self, values):
        return statistics.mean(values)

    @stat_property
    def stdev(self, values):
        return statistics.stdev(values)
