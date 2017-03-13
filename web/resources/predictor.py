from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.predictor import Predictor, PredictorEvent

# Predictor Resources
class PredictorSchema(Schema):
	id = fields.Str(dump_only=True)

	predictor_events = fields.Nested(PredictorEventSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Predictor(**data)

	class Meta:
		additional = ('name', 'description', 'run_id', 'analysis_id')

class PredictorResource(Resource):
	""" Predictors """
	@operation(
	responseMessages=[
	    {
	      "code": 400,
	      "message": "Predictor doesn't exist"
	    },
	  ]
	)
	@jwt_required()
	def get(self, id):
		""" Access a predictor by id """
		result = Predictor.query.filter_by(id=id).one()
		if result:
			return PredictorSchema().dump(result)
		else:
			abort(400, message="Predictor {} doesn't exist".format(id))

# This might not be necessary, unless you can query by run,
# which might violate standard REST
class PredictorListResource(Resource):
	""" Extracted predictors """
	@operation()
	@jwt_required()
	def get(self):
		""" List of extracted predictors """
		result = Predictor.query.filter_by().all()
		return PredictorSchema(many=True).dump(result)

# Predictor Event Resources
class PredictorEventSchema(Schema):
	id = fields.Str(dump_only=True)

	@post_load
	def make_db(self, data):
		return Predictor(**data)

	class Meta:
		additional = ('onset', 'duraton', 'value')
