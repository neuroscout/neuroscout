from flask_apispec import MethodResource, marshal_with, use_kwargs, doc
from webargs import fields
from ..models import Run
from .utils import first_or_404
from ..schemas.run import RunSchema


class RunResource(MethodResource):
    @doc(tags=['run'], summary='Get run by id.')
    @marshal_with(RunSchema())
    def get(self, run_id):
        return first_or_404(Run.query.filter_by(id=run_id))


class RunListResource(MethodResource):
    @doc(tags=['run'], summary='Returns list of runs.')
    @use_kwargs({
        'session': fields.DelimitedList(
            fields.Str(), description='Session number(s).'),
        'number': fields.DelimitedList(
            fields.Int(), description='Run number(s).'),
        'task_id': fields.DelimitedList(
            fields.Int(), description='Task id(s).'),
        'subject': fields.DelimitedList(
            fields.Str(), description='Subject id(s).'),
        'dataset_id': fields.Int(description='Dataset id.'),
    }, location='query')
    @marshal_with(RunSchema(many=True))
    def get(self, **kwargs):
        try:
            dataset = kwargs.pop('dataset_id')
        except KeyError:
            dataset = None

        query = Run.query
        for param in kwargs:
            query = query.filter(getattr(Run, param).in_(kwargs[param]))

        if dataset:
            query = query.join('dataset').filter_by(id=dataset)
        return query.all()


class RunTimingResource(MethodResource):
    @doc(tags=['run'], summary='Get stimulus timing for a run.')
    def get(self, run_id):
        stim_paths  = Stimulus.query.filter(Stimulus.mimetype.like('video%')).join(
            RunStimulus).filter_by(run_id=r.id).with_entities('Stimulus.path', 'run_stimulus.onset').all()

        return [{'filename': s[0].split('/')[-1], 'onset': s[1]} for s in stim_paths]
