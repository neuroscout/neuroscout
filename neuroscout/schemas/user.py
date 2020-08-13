from flask_security.utils import encrypt_password
from marshmallow import (
    Schema, fields, validates, ValidationError, post_load, post_dump)
from ..models import User


class UserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, description='User full name')
    user_name = fields.Str(description='User name')
    password = fields.Str(load_only=True,
                          description='Password. Minimum 6 characters.')
    picture = fields.Str(allow_none=True,
                         description='Links to avatar.')
    personal_site = fields.Str(allow_none=True,
                               description='Site URL.')
    twitter_handle = fields.Str(allow_none=True,
                                description='Twitter handle.')
    orcid = fields.Str(allow_none=True,
                       description='ORCID')
    public_email = fields.Bool(description='Display email in public profile.')

    predictor_collections = fields.Nested(
        'PredictorCollectionSchema', only=['id', 'collection_name'],
        description='Predictor collections contributed by this user.',
        many=True, dump_only=True)
    first_login = fields.Bool(description='First time logging in.')
    institution = fields.Str(allow_none=True)

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


class UserPublicSchema(UserSchema):
    @post_dump
    def redact_email(self, out_data):
        if not out_data['public_email']:
            out_data['email'] = 'HIDDEN'
        return out_data


class UserCreationSchema(UserSchema):
    password = fields.Str(load_only=True, required=True,
                          description='Password. Minimum 6 characters.')

    @validates('email')
    def validate_name(self, value):
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already in use.')


class UserResetSchema(UserCreationSchema):
    token = fields.Str(required=True, description="Password reset token.")
