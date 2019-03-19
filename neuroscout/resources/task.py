from marshmallow import Schema, fields
from flask_apispec import MethodResource, marshal_with, doc, use_kwargs
from models import Task
import webargs as wa
from .utils import first_or_404

class TaskSchema(Schema):
    id = fields.Int()
    name = fields.Str()

    dataset_id = fields.Int()
    num_runs = fields.Int(description='Number of runs.')
    TR = fields.Number()
    summary = fields.Str(description='Task summary description')


class TaskResource(MethodResource):
    @doc(tags=['run'], summary='Get task by id.')
    @marshal_with(TaskSchema)
    def get(self, task_id):
        return first_or_404(Task.query.filter_by(id=task_id))


class TaskListResource(MethodResource):
    @doc(tags=['run'], summary='Returns list of tasks.')
    @use_kwargs({
        'dataset_id': wa.fields.Int(description='Dataset id(s).'),
    }, locations=['query'])
    @marshal_with(TaskSchema(many=True))
    def get(self, **kwargs):
        query = Task.query
        for param in kwargs:
            query = query.filter(getattr(Task, param) == kwargs[param])
        return query.all()
