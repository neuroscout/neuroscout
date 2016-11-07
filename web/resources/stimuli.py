from flask_restful import Resource
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.stimulus import Stimulus

class StimulusSchema(Schema):
	id = fields.Str(dump_only=True)
	# timelines = fields.Nested(TimelineSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Stimulus(**data)

	class Meta:
		additional = ('dataset_id', )

class StimulusResource(Resource):
	@jwt_required()
	def get(self, extractor_id):
		pass
	def put(self, extractor_id):
		pass

class StimulusListResource(Resource):
	@jwt_required()
	def get(self):
		pass
	def put(self):
		pass