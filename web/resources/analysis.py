from flask import request
from flask_restful import Resource, abort
from flask_restful_swagger.swagger import operation
from flask_jwt import jwt_required
from marshmallow import Schema, fields, post_load, validates, ValidationError
from models.analysis import Analysis
from database import db


from .event import EventSchema
from .predictor import PredictorSchema
from .result import ResultSchema

class AnalysisSchema(Schema):
	id = fields.Str(dump_only=True)
	results = fields.Nested(ResultSchema, many=True, only='id')
	name = fields.Str(required=True)
	description = fields.Str(required=True)
	events = fields.Nested(EventSchema, many=True, only='id')
	predictors = fields.Nested(PredictorSchema, many=True, only='id')

	@post_load
	def make_db(self, data):
		return Analysis(**data)

	class Meta:
		additional = ('dataset_id', 'user_id', 'parent')

class AnalysisResource(Resource):
	""" This is a user generated analysis """
	@operation(
	notes='analyses are useful',
	nickname='analysis',
	parameters=[
	    {
	      "name": "Analysis",
	      "description": "A user generate analysis",
	      "required": True,
	      "allowMultiple": False,
	      "dataType": Analysis.__name__,
	      "paramType": "body"
	    }
	  ],
	responseMessages=[
	    {
	      "code": 400,
	      "message": "Analysis doesn't exist"
	    },
	  ]
	)
	@jwt_required()
	def get(self, analysis_id):
		result = Analysis.query.filter_by(id=analysis_id).one()
		if result:
			return AnalysisSchema().dump(result)
		else:
			abort(400, message="Analysis {} doesn't exist".format(analysis_id))


class AnalysisListResource(Resource):
	""" User-generated analyses """
	@operation()
	@jwt_required()
	def get(self):
		""" Get a list of existing analyses """
		result = Analysis.query.filter_by().all()
		return AnalysisSchema(many=True).dump(result)

	@operation(
	responseMessages=[
	    {
	      "code": 405,
	      "message": "Invalid input"
	    },
	  ]
	)
	@jwt_required()
	def post(self):
		""" Post a new analysis """
		new, errors = AnalysisSchema().load(request.get_json())

		if errors:
			abort(405 , errors=errors)
		else:
			db.session.add(new)
			db.session.commit()

	## Return some information like the analysis id

	