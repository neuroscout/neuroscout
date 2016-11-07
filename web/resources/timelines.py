from flask_restful import Resource
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.timeline import Timeline

class TimelineSchema(Schema):
	id = fields.Str(dump_only=True)
	# timelines = fields.Nested(TimelineSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Result(**data)

	class Meta:
		additional = ('dataset_id', )

class TimelineResource(Resource):
	@jwt_required()
	def get(self, extractor_id):
		pass
	def put(self, extractor_id):
		pass

class TimelineListResource(Resource):
	@jwt_required()
	def get(self):
		pass
	def put(self):
		pass