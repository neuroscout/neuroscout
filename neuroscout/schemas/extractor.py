from marshmallow import fields, Schema


class ExtractorSchema(Schema):
    """ Extractor documentation schema. """
    name = fields.Str(description='Extractor name')
    description = fields.Str(description='Extractor description')