from marshmallow import fields, Schema


class TaskSchema(Schema):
    id = fields.Int()
    name = fields.Str()

    dataset_id = fields.Int()
    n_subjects = fields.Int(
        description='Number of unique subjects')
    TR = fields.Number()
    summary = fields.Str(description='Task summary description')
