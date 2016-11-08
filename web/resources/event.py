from flask_restful import Resource, abort
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.event import Event, Predictor

class EventSchema(Schema):
	id = fields.Str(dump_only=True)

	@post_load
	def make_db(self, data):
		return Event(**data)

	class Meta:
		additional = ('extractor_id', 'analysis_id', 'stimuli_id')

class EventResource(Resource):
	@jwt_required()
	def get(self, timeline_id):
		result = Event.query.filter_by(id=timeline_id).one()
		if result:
			return EventSchema().dump(result)
		else:
			abort(400, message="Event {} doesn't exist".format(timeline_id))

class EventListResource(Resource):
	@jwt_required()
	def get(self):
		pass


class PredictorSchema(Schema):
	id = fields.Str(dump_only=True)
	stimuli = fields.Nested(EventSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Event(**data)

	class Meta:
		additional = ('stimulus_id', 'extractor_id')

class PredictorResource(Resource):
	@jwt_required()
	def get(self, timeline_id):
		result = Predictor.query.filter_by(id=timeline_id).one()
		if result:
			return PredictorSchema().dump(result)
		else:
			abort(400, message="Predictor {} doesn't exist".format(timeline_id))

class PredictorListResource(Resource):
	@jwt_required()
	def get(self):
		pass