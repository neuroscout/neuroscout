from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.event import Event

class EventSchema(Schema):
	id = fields.Str(dump_only=True)

	@post_load
	def make_db(self, data):
		return Event(**data)

	class Meta:
		additional = ('stimulus_id', 'predictor_id', 'analysis_id', 'onset', 'duration', 'amplitude')

class EventResource(Resource):
	""" Individual event """
	@operation(
	responseMessages=[
	    {
	      "code": 400,
	      "message": "Event doesn't exist"
	    },
	  ]
	)
	@jwt_required()
	def get(self, event_id):
		""" Access individual event """
		result = Event.query.filter_by(id=event_id).one()
		if result:
			return EventSchema().dump(result)
		else:
			abort(400, message="Event {} doesn't exist".format(event_id))
