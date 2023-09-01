from marshmallow import fields, Schema


class DatasetSchema(Schema):
    """ Dataset validation schema. """
    id = fields.Int()
    name = fields.Str(
        description='Dataset name')
    description = fields.Dict(
        description='Dataset description from BIDS dataset')
    long_description = fields.Dict(
        description='Long description of dataset')
    summary = fields.Str(
        description='Dataset summary description')
    url = fields.Str(
        description='Link to external resources')
    mimetypes = fields.List(
        fields.Str(), description='Dataset mimetypes/modalities')
    mean_age = fields.Float(
        description='Mean age in years of subjects')
    percent_female = fields.Float(
        description='Percent female subjects')
    runs = fields.Pluck(
        'RunSchema', 'id', many=True)
    tasks = fields.Nested(
        'TaskSchema', many=True,
        only=['id', 'name', 'summary', 'n_subjects', 'n_runs_subject',
              'avg_run_duration', 'TR'])
    dataset_address = fields.Str(
        description='BIDS Dataset remote address')
    preproc_address = fields.Str(
        description='Preprocessed data remote address')
    active = fields.Boolean(
        description='Dataset is currently available for model creation')
