from flask_jwt import current_identity
from flask_security.utils import encrypt_password

from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from marshmallow import Schema, fields, validates, ValidationError, post_load
from models.auth import User
from database import db
from auth import register_user
from models import user_datastore
from . import utils
import db_utils
from .utils import abort

class UserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, description='User full name')
    password = fields.Str(load_only=True,
                          description='Password. Minimum 6 characters.')

    analyses = fields.Nested('AnalysisSchema', only=['hash_id', 'name', 'status',
                                                     'description', 'modified_at'],
                             many=True, dump_only=True)

    @validates('password')
    def validate_pass(self, value):
    	if len(value) < 6:
    		raise ValidationError('Password must be at least 6 characters.')

    @post_load
    def encrypt_password(self, in_data):
        if 'password' in in_data:
            in_data['password'] = encrypt_password(in_data['password'])
        return in_data

    class Meta:
        strict = True

class UserCreationSchema(UserSchema):
    password = fields.Str(load_only=True, required=True,
                          description='Password. Minimum 6 characters.')

    @validates('email')
    def validate_name(self, value):
    	if User.query.filter_by(email=value).first():
    		raise ValidationError('Email already in use.')



@doc(tags=['auth'])
@marshal_with(UserSchema)
class UserRootResource(MethodResource):
    @doc(summary='Get current user information.')
    @utils.auth_required
    def get(self):
    	return current_identity

    @doc(summary='Add a new user.')
    @use_kwargs(UserCreationSchema)
    def post(self, **kwargs):
        return register_user(**kwargs)

    @doc(summary='Edit user information.')
    @use_kwargs(UserSchema)
    @utils.auth_required
    def put(self, **kwargs):
        if User.query.filter((User.email==kwargs['email']) \
                             & (User.id!=current_identity.id)).all():
            abort(422, 'Email already in use.')
        return db_utils.put_record(db.session, kwargs, current_identity)
