from flask import request
from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required, current_identity
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.auth import User
from database import db

from .analysis import AnalysisSchema
from db_utils import put_record

class UserSchema(Schema):
	analyses = fields.Nested(AnalysisSchema, many=True, dump_only=True)
	last_login_at = fields.DateTime(dump_only = True)

	class Meta:
		additional = ('email', )

class UserResource(Resource):
	""" Current user data """
	@jwt_required()
	def get(self):
		""" Get user info """
		return UserSchema().dump(current_identity)

	@jwt_required()
	def put(self):
		""" Get user info """
		### This could maybe be a patch request instead, esp given nested fields
		updated, errors = UserSchema().load(request.get_json())

		if errors:
			abort(405 , errors=errors)
		else:
			put_record(db.session, updated, current_identity)

