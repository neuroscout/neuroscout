from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.result import Result

class ResultSchema(Schema):
	id = fields.Str(dump_only=True)

	@post_load
	def make_db(self, data):
		return Result(**data)

	class Meta:
		additional = ('analysis_id', )

class ResultResource(Resource):
	@operation()
	@jwt_required()
	def get(self, result_id):
		result = Result.query.filter_by(id=result_id).one()
		if result:
			return ResultSchema().dump(result)
		else:
			abort(400, message="Result {} doesn't exist".format(result_id))

class ResultListResource(Resource):
	@operation()
	@jwt_required()
	def get(self):
		result = Result.query.filter_by().all()
		return ResultSchema(many=True).dump(result)
