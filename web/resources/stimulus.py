from marshmallow import Schema, fields
from models.stimulus import Stimulus
from flask_apispec import MethodResource, marshal_with

class StimulusSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    mimetype = fields.Str(dump_only=True)
    path = fields.Str(dump_only=True)

class StimulusResource(MethodResource):
    @marshal_with(StimulusSchema)
    def get(self, stimulus_id):
        """ Stimulus list.
        ---
        get:
        	summary: Get list of stimuli.
        	responses:
        		200:
        			description: successful operation
        			schema: StimulusSchema
        """
        return Stimulus.query.filter_by(id=stimulus_id).first_or_404()
