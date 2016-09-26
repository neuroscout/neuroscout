from flask_restful import Resource
from flask_jwt import jwt_required

class HelloWorld(Resource):
	@jwt_required()
	def get(self):
		return {'hello': 'world'}