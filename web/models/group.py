from database import db

class GroupPredictor(db.Model):
    """ Group-level predictors, e.g. across subjects, sessions, etc... """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text) # Where to get this from?
    level = db.Column(db.String, nullable=False) # Session? Subject?

    dataset_id = db.Column(db.Text, db.ForeignKey('dataset.id'), nullable=False)

    values = db.relationship('GroupPredictorValue', backref='group_predictor',
								lazy='dynamic')


class GroupPredictorValue(db.Model):
    """ Contains values of GroupPredictor for every Run.
        Also an association table between these two tables. """
    gp_id = db.Column(db.Integer, db.ForeignKey('group_predictor.id'),
                      primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), primary_key=True)
    level_id = db.Column(db.String, primary_key=True)
    value = db.Column(db.String, nullable=False)
