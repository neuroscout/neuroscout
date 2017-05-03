from marshmallow import Schema, fields
from models.stimulus import Stimulus
from flask_apispec import MethodResource, marshal_with, doc

class StimulusSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    mimetype = fields.Str(dump_only=True, description='modality/mimetype')

class StimulusResource(MethodResource):
    @doc(tags=['stimulus'], summary='Get stimulus by id.')
    @marshal_with(StimulusSchema)
    def get(self, stimulus_id):
        return Stimulus.query.filter_by(id=stimulus_id).first_or_404()
