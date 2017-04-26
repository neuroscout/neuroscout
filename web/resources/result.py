from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load
from models.result import Result

class ResultSchema(Schema):
	id = fields.Str(dump_only=True)

	@post_load
	def make_db(self, data):
		return Result(**data)

	class Meta:
		additional = ('analysis_id', )
#
# class ResultResource(Resource):
# 	""" Analysis result """
# 	@operation()
# 	@jwt_required()
# 	def get(self, result_id):
# 		""" Access analyis result """
# 		result = Result.query.filter_by(id=result_id).first_or_404()
# 		return ResultSchema().dump(result)
#
# class ResultListResource(Resource):
# 	""" Analysis results """
# 	@operation()
# 	@jwt_required()
# 	def get(self):
# 		""" List of available results """
# 		result = Result.query.filter_by().all()
# 		return ResultSchema(many=True).dump(result)
