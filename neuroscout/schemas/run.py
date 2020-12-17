from marshmallow import fields, Schema


class RunSchema(Schema):
    id = fields.Int()
    session = fields.Str(description='Session number')
    acquisition = fields.Str(description='Acquisition')
    subject = fields.Str(description='Subject id')
    number = fields.Int(description='Run id')
    duration = fields.Number(description='Total run duration in seconds.')
    dataset_id = fields.Int(description='Dataset run belongs to.')
    task = fields.Pluck(
        'TaskSchema', 'id', description="Task id")
    task_name = fields.Pluck(
        'TaskSchema', 'name', description="Task name")
