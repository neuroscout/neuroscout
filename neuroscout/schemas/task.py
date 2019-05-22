from marshmallow import fields, Schema


class TaskSchema(Schema):
    id = fields.Int()
    name = fields.Str()

    dataset_id = fields.Int()
    num_runs = fields.Int(description='Number of runs.')
    TR = fields.Number()
    summary = fields.Str(description='Task summary description')
