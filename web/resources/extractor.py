from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.extractor import Extractor

from sqlalchemy.orm.exc import NoResultFound

class ExtractorSchema(Schema):
	id = fields.Str(dump_only=True)

	class Meta:
		# How many of these should be required
		additional = ('name', 'description', 'version', 'input_type', 'output_type')

class ExtractorResource(Resource):
	""" Individual extractor """
	@operation(
	responseMessages=[
	    {
	      "code": 400,
	      "message": "Extractor does not exist"
	    },
	  ]
	)
	@jwt_required()
	def get(self, extractor_id):
		""" Access an extractor """
		try:
			result = Extractor.query.filter_by(id=extractor_id).one()
			return ExtractorSchema().dump(result)
		except NoResultFound:
			abort(400, message="Extractor {} does not exist".format(extractor_id))

class ExtractorListResource(Resource):
	""" Available extractors """
	@operation()
	@jwt_required()
	def get(self):
		""" Get list of available extractors """
		result = Extractor.query.filter_by().all()
		return ExtractorSchema(many=True).dump(result)
