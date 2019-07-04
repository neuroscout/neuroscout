from flask_security.utils import encrypt_password
from marshmallow import Schema, fields, validates, ValidationError, post_load
from ..models import User


class UserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, description='User full name')
    password = fields.Str(load_only=True,
                          description='Password. Minimum 6 characters.')
    picture = fields.Str(allow_none=True)
    analyses = fields.Nested('AnalysisSchema',
                             only=['hash_id', 'name', 'status',
                                   'description', 'modified_at', 'dataset_id'],
                             many=True, dump_only=True)
    first_login = fields.Bool(description='First time logging in.')

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


class UserResetSchema(UserCreationSchema):
    token = fields.Str(required=True, description="Password reset token.")
