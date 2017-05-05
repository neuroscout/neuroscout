from marshmallow import Schema, fields
from flask_apispec import MethodResource, marshal_with, doc
from models import Task

class TaskSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    description = fields.Dict(dump_only=True,
                                   description='BIDS task description')

    dataset_id = fields.Int()
    runs = fields.Nested('RunSchema', only=['id', 'name'])

class TaskResource(MethodResource):
    @doc(tags=['stimulus'], summary='Get stimulus by id.')
    @marshal_with(TaskSchema)
    def get(self, stimulus_id):
        return Task.query.filter_by(id=stimulus_id).first_or_404()
