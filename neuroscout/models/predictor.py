from sqlalchemy import cast, func, Float, desc
from ..database import db
from .features import ExtractedEvent, ExtractedFeature
from .stimulus import Stimulus
import datetime
import numpy as np


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

    predictor_collection_id = db.Column(
        db.Integer, db.ForeignKey('predictor_collection.id'))

    predictor_run = db.relationship('PredictorRun')
    active = db.Column(db.Boolean, default=True)  # Actively display or not
    private = db.Column(db.Boolean, default=False)
    
    @property
    def float_values(self):
        if self.extracted_feature:
            key = self.extract_features.extracted_events
        else:
            key = self.predictor_events
            
        try:
            vals = [float(ee.value) for ee in key]
        except:
            vals = None
        return vals
    @property
    def max(self):
        vals = self.float_values
        if vals:
            vals =  max(vals)
        return vals

    @property
    def min(self):
        vals = self.float_values
        if vals:
            vals =  min(vals)
        return vals

    @property
    def num_na(self):
        vals = self.float_values
        if vals:
            vals = len([v for v in vals if v == 'n/a'])
        return vals
    @property
    def mean(self):
        vals = self.float_values
        if vals:
            vals = np.mean(vals)
        return res

    def get_top_bottom(self, bottom=False, limit=None):
        """ Get the Stimuli associated with the top or botton N values for this Predictor """
        try:
            val = cast(ExtractedEvent.value, Float)
            if bottom:
                val = desc(val)
            res = Stimulus.query.join(ExtractedEvent).filter_by(ef_id=self.ef_id).order_by(val).limit(limit).all()
        except:
            res = None
        return res

    def __repr__(self):
        return '<models.Predictor[name=%s]>' % self.name


class PredictorEvent(db.Model):
    """ An event within a Predictor. Onset is relative to run. """
    id = db.Column(db.Integer, primary_key=True)

    onset = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float)
    value = db.Column(db.String, nullable=False)
    object_id = db.Column(db.Integer)

    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False,
                       index=False)
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


class PredictorCollection(db.Model):
    """ Predictor Collection Upload """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    predictors = db.relationship('Predictor', backref='predictor_collection')

    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    collection_name = db.Column(db.Text, nullable=False)

    task_id = db.Column(db.Text)
    traceback = db.Column(db.Text)
    status = db.Column(db.Text, default='PENDING')
    __table_args__ = (
        db.CheckConstraint(status.in_(['OK', 'FAILED', 'PENDING'])), )

    def __repr__(self):
        return '<models.PredictorCollection[uploaded_at={} status={}]>'.format(
            self.uploaded_at, self.status)
