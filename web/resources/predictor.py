from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields
from models.predictor import Predictor

# Predictor Event Resources
class PredictorEventSchema(Schema):
	id = fields.Str(dump_only=True)

	class Meta:
		additional = ('onset', 'duration', 'value', 'run_id', 'predictor_id')

# Predictor Resources
class PredictorSchema(Schema):
	id = fields.Str(dump_only=True)

	predictor_events = fields.Nested(PredictorEventSchema, many=True, only='id')

	class Meta:
		additional = ('name', 'description', 'ef_id', 'analysis_id')

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
