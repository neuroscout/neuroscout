from marshmallow import Schema, fields
from flask_apispec import MethodResource, marshal_with, doc
from models import Task

class TaskSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    description = fields.Dict(description='BIDS task description')

    dataset_id = fields.Int()
    runs = fields.Nested('RunSchema', only=['id'])
    num_runs = fields.Int(description='Number of runs.')

class TaskResource(MethodResource):
    @doc(tags=['run'], summary='Get task by id.')
    @marshal_with(TaskSchema)
    def get(self, task_id):
        return Task.query.filter_by(id=task_id).first_or_404()
