from ..database import db
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore

# Association table between users and runs.
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class User(db.Model, UserMixin):
    """" User model class """
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.Text)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    user_name = db.Column(db.Text, unique=True)

    name = db.Column(db.Text)
    picture = db.Column(db.Text)
    institution = db.Column(db.Text)
    personal_site = db.Column(db.Text)
    twitter_handle = db.Column(db.Text)
    orcid = db.Column(db.Text)
    public_email = db.Column(db.Boolean(), default=True)

    active = db.Column(db.Boolean())  # If set to disabled, cannot access.
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users'))
    last_activity_at = db.Column(db.DateTime())
    last_activity_ip = db.Column(db.String(255))

    analyses = db.relationship('Analysis', backref='user')
    predictor_collections = db.relationship('PredictorCollection')
    first_login = db.Column(db.Boolean(), default=True)

    def __repr__(self):
        return '<models.User[email=%s]>' % self.email


class Role(db.Model, RoleMixin):
    """ User roles """
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
