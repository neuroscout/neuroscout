from flask_jwt import current_identity
from flask_security.utils import encrypt_password

from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from marshmallow import Schema, fields, validates, ValidationError
from models.auth import User
from database import db
from models import user_datastore
from . import utils
from db_utils import put_record
from .utils import abort

### Make user creation class and a regular user class
class BaseUserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, description='User full name')

    @validates('password')
    def validate_pass(self, value):
    	if len(value) < 6:
    		raise ValidationError('Password must be at least 6 characters.')

    class Meta:
        strict = True

class UserCreationSchema(BaseUserSchema):
    password = fields.Str(load_only=True, required=True,
                          description='Password. Minimum 6 characters.')

    @validates('email')
    def validate_name(self, value):
    	if User.query.filter_by(email=value).count() != 0:
    		raise ValidationError('This email is already associated with an acccount.')


class UserSchema(BaseUserSchema):
    password = fields.Str(load_only=True,
                          description='Password. Minimum 6 characters.')
    last_login_at = fields.DateTime(dump_only= True)

    analyses = fields.Nested('AnalysisSchema', only='id',
                             many=True, dump_only=True)


@doc(tags=['auth'])
class UserRootResource(MethodResource):
    @doc(summary='Get current user information.')
    @utils.auth_required
    @marshal_with(UserSchema)
    def get(self):
    	return current_identity

    @doc(summary='Add a new user.')
    @use_kwargs(UserSchema)
    @marshal_with(UserCreationSchema)
    def post(self, **kwargs):
        if 'password' not in kwargs:
            abort(422, 'Password required')
        else:
            kwargs['password'] = encrypt_password(kwargs['password'])
        user = user_datastore.create_user(**kwargs)
        db.session.commit()
        return user

    @doc(summary='Edit user information.')
    @use_kwargs(UserSchema)
    @utils.auth_required
    @marshal_with(UserSchema)
    def put(self, **kwargs):
        ### ABSTRACT THIS TO MARSHMALLOW SCHEMA
        if 'password' in kwargs:
            kwargs['password'] = encrypt_password(kwargs['password'])

        ### CAN I DO NOT EQUAL IN FILTER BY?
        email_match = User.query.filter_by(email=kwargs['email']).first()
        if email_match and email_match.id != current_identity.id:
            abort(422, 'Email already in use by another user.')
        return put_record(db.session, kwargs, current_identity)
