from marshmallow import fields, Schema


class TaskSchema(Schema):
    id = fields.Int()
    name = fields.Str()

    dataset_id = fields.Int()
    n_subjects = fields.Int(
        description='Number of unique subjects')
    n_runs_subject = fields.Int(
        description='Number of runs per subject')
    avg_run_duration = fields.Int(
        description='Average run duration in seconds')
    TR = fields.Number(
        description='Repetition Time')
    summary = fields.Str(
        description='Task summary description')
    runs = fields.Pluck(
        'RunSchema', 'id', many=True)
