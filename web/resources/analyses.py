from flask_restful import Resource
from flask_jwt import jwt_required

class AnalysisResource(Resource):
	@jwt_required()
	def get(self, analysis_id):
		pass

	def put(self, analysis_id):
		pass

	def delete(self, analysis_id):
		pass

class AnalysisListResource(Resource):
	@jwt_required()
	def get(self):
		pass

	def put(self):
		pass

# class AnalysisSchema(Schema):
	


### Write Schemas for each model (maybe place them in  here? with flask-marshmallow)