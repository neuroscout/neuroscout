from flask import request
from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required, current_identity
from flask_security.utils import encrypt_password

from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.auth import User
from database import db
from models.auth import user_datastore

from .analysis import AnalysisSchema
from db_utils import put_record

class UserSchema(Schema):
	analyses = fields.Nested(AnalysisSchema, many=True, dump_only=True)
	last_login_at = fields.DateTime(dump_only = True)
	email = fields.Email(required=True)
	name = fields.Str(required=True)

class NewUserSchema(Schema):
	password = fields.Str(load_only=True, required=True)
	email = fields.Email(required=True)
	name = fields.Str(required=True)

	@post_load
	def create_user(self, data):
		data['password']= encrypt_password(data['password'])
		user_datastore.create_user(**data)
		db.session.commit()

	@validates('email')
	def validate_name(self, value):
		if User.query.filter_by(email=value).count() > 0:
			raise ValidationError('This email is already associated with an acccount.')

	class Meta:
		additional = ('name', )

class UserResource(Resource):
	""" Current user data """
	@operation()
	@jwt_required()
	def get(self):
		""" Get user info """
		return UserSchema().dump(current_identity)

	@operation(
	responseMessages=[{"code": 400, "message": "Bad request"}])
	@jwt_required()
	def put(self):
		""" Update user info """
		### This could maybe be a patch request instead, esp given nested fields
		updated, errors = UserSchema().load(request.get_json())
		print(updated)

		if errors:
			abort(400 , errors=errors)
		else:
			put_record(db.session, updated, current_identity)

	@operation(
	responseMessages=[{"code": 400, "message": "Bad request"}])
	def post(self):
		""" Create a new user """
		new, errors = NewUserSchema().load(request.get_json())

		if errors:
			abort(400 , errors=errors)
