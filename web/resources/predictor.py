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
	@operation()
	@jwt_required()
	def get(self, id):
		""" Access a predictor by id """
		result = Predictor.query.filter_by(id=id).one_or_404()
		return PredictorSchema().dump(result)

class PredictorListResource(Resource):
	""" Extracted predictors """
	@operation()
	@jwt_required()
	def get(self):
		""" List of extracted predictors """
		result = Predictor.query.filter_by().all()
		return PredictorSchema(many=True).dump(result)
