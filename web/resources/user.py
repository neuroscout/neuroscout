from flask_jwt import jwt_required, current_identity
from flask_security.utils import encrypt_password

from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from marshmallow import Schema, fields, validates, ValidationError
from models.auth import User
from database import db
from models.auth import user_datastore

from .analysis import AnalysisSchema
# from db_utils import put_record

class UserSchema(Schema):
    name = fields.Str(required=True, description='User full name')
    email = fields.Email(required=True)
    password = fields.Str(load_only=True, required=True,
                          description='Password. Minimum 6 characters.')
    last_login_at = fields.DateTime(dump_only= True)

    analyses = fields.Nested(AnalysisSchema, only='id',
                             many=True, dump_only=True)

    @validates('email')
    def validate_name(self, value):
    	if User.query.filter_by(email=value).count() > 0:
    		raise ValidationError('This email is already associated with an acccount.')

    @validates('password')
    def validate_pass(self, value):
    	if len(value) < 6:
    		raise ValidationError('Password must be at least 6 characters.')

    class Meta:
        strict = True

class UserResource(MethodResource):
    @doc(tags=['auth'], summary='Get current user information.')
    @marshal_with(UserSchema)
    @jwt_required()
    def get(self):
    	return current_identity

class UserPostResource(MethodResource):
    @doc(tags=['auth'], summary='Add a new user.')
    @marshal_with(UserSchema)
    @use_kwargs(UserSchema)
    def post(self, **kwargs):
        kwargs['password']= encrypt_password(kwargs['password'])
        user = user_datastore.create_user(**kwargs)
        db.session.commit()
        return user

    # MAY NEED TWO SCHEMAS, one for patch and for post
	# def put(self):
	# 	""" Update user info """
	# 	### This could maybe be a patch request instead, esp given nested fields
	# 	updated, errors = UserSchema().load(request.get_json())
	# 	print(updated)
    #
	# 	put_record(db.session, updated, current_identity)
