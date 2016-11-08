from flask_restful import Resource, abort
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.extractor import Extractor

class ExtractorSchema(Schema):
	id = fields.Str(dump_only=True)

	class Meta:
		# How many of these should be required
		additional = ('name', 'description', 'version', 'input_type', 'output_type')

class ExtractorResource(Resource):
	@jwt_required()
	def get(self, extractor_id):
		result = Extractor.query.filter_by(id=extractor_id).one()
		if result:
			return ExtractorSchema().dump(result)
		else:
			abort(400, message="Extractor {} doesn't exist".format(extractor_id))

class ExtractorListResource(Resource):
	@jwt_required()
	def get(self):
		result = Extractor.query.filter_by().all()
		return ExtractorSchema(many=True).dump(result)
