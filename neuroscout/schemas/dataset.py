from marshmallow import fields, Schema


class DatasetSchema(Schema):
    """ Dataset validation schema. """
    id = fields.Int()
    name = fields.Str(
        description='Dataset name')
    description = fields.Dict(
        description='Dataset description from BIDS dataset')
    summary = fields.Str(
        description='Dataset summary description')
    url = fields.Str(
        descrption='Link to external resources')
    mimetypes = fields.List(
        fields.Str(), description='Dataset mimetypes/modalities')
    runs = fields.Nested(
        'RunSchema', many=True, only='id')
    tasks = fields.Nested(
        'TaskSchema', many=True, only=['id', 'name', 'summary', 'num_runs'])
    dataset_address = fields.Str(
        description='BIDS Dataset remote address')
    preproc_address = fields.Str(
        description='Preprocessed data remote address')
    active = fields.Boolean(
        description='Dataset is currently available for model creation')
    n_subjects = fields.Int(
        description='Number of unique subjects')
