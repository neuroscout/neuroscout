from flask_restful import Resource
from flask_jwt import jwt_required

class Analyses(Resource):
	@jwt_required()
	def get(self):
		pass
		
	def put(self):
		pass