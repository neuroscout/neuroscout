from ..database import db
from .group import GroupPredictor, GroupPredictorValue
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from .stimulus import Stimulus
import statistics


class Dataset(db.Model):
    """ A BIDS dataset """
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(JSONB)  # BIDS description
    summary = db.Column(db.Text)  # Hand crafted summary
    long_description = db.Column(db.Text) # Custom long description
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
        return [
            x[1]
            for x in sorted(
                Stimulus.query.filter_by(
                    dataset_id=self.id).distinct(
                        'mimetype').values('id', 'mimetype'))
            ]

    @hybrid_property
    def mean_age(self):
        try:
            val = GroupPredictorValue.query.join(GroupPredictor).filter_by(
                dataset_id=self.id, name='age').values('value')
            # Translating age ranges to
            age_map = {'20-25': 22.5, '25-30': 27.5, '30-35': 32.5, '35-40': 37.5}
            vals = []
            for v in val:
                if v[0] in age_map:
                    vals.append(age_map[v[0]])
                else:
                    vals += [float(v) for v in v.split(",")]
        except ValueError:
            return None

        if vals:
            return statistics.mean(vals)
        else:
            return None

    @hybrid_property
    def percent_female(self):
        values = GroupPredictorValue.query.join(GroupPredictor).filter_by(
            dataset_id=self.id).filter(
                GroupPredictor.name.in_(['gender', 'sex'])).values('value')
        fem = [1 if v[0] in ['f', 'F'] else 0 for v in values]

        if fem:
            return statistics.mean(fem)
        else:
            return None

    # Meta-data, such as preprocessed history, etc...
    def __repr__(self):
        return '<models.Dataset[name=%s]>' % self.name
