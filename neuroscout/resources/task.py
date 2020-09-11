from flask_apispec import MethodResource, marshal_with, doc, use_kwargs
from ..models import Task
from webargs import fields
from .utils import first_or_404
from ..schemas.task import TaskSchema


class TaskResource(MethodResource):
    @doc(tags=['run'], summary='Get task by id.')
    @marshal_with(TaskSchema)
    def get(self, task_id):
        return first_or_404(Task.query.filter_by(id=task_id))


class TaskListResource(MethodResource):
    @doc(tags=['run'], summary='Returns list of tasks.')
    @use_kwargs({
        'dataset_id': fields.Int(description='Dataset id(s).'),
    }, location='query')
    @marshal_with(TaskSchema(many=True))
    def get(self, **kwargs):
        query = Task.query
        for param in kwargs:
            query = query.filter(getattr(Task, param) == kwargs[param])
        return query.all()
