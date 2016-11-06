from flask_restful import Resource
from flask_jwt import jwt_required

class ExtractorResource(Resource):
	@jwt_required()
	def get(self, extractor_id):
		pass
	def put(self, extractor_id):
		pass

class ExtractorListResource(Resource):
	@jwt_required()
	def get(self):
		pass
	def put(self):
		pass