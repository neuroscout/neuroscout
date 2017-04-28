from marshmallow import Schema, fields
from models.result import Result
from flask_apispec import MethodResource, marshal_with

class ResultSchema(Schema):
    id = fields.Str(dump_only=True)
    analysis_id = fields.Int(dump_only=True)

class ResultResource(MethodResource):
    @marshal_with(ResultSchema)
    def get(self, result_id):
        """ Result.
        ---
    	get:
    		summary: Get Result by id.
    		responses:
    			200:
    				description: successful operation
    				schema: ResultSchema
        """
        return Result.query.filter_by(id=result_id).first_or_404()

class ResultListResource(MethodResource):
    @marshal_with(ResultSchema(many=True))
    def get(self):
        """ Result list.
        ---
    	get:
    		summary: Get list of results.
    		responses:
    			200:
    				description: successful operation
    				schema: ResultSchema
        """
        return Result.query.filter_by().all()
