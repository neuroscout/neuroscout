from marshmallow import Schema, fields
from flask_apispec import MethodResource, marshal_with, doc
from models import Result

class ResultSchema(Schema):
    id = fields.Str(dump_only=True)
    analysis_id = fields.Int(dump_only=True)

class ResultResource(MethodResource):
    @marshal_with(ResultSchema)
    @doc(tags=['result'], summary='Get Result by id.')
    def get(self, result_id):
        return Result.query.filter_by(id=result_id).first_or_404()
