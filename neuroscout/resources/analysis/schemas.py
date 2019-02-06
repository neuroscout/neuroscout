from marshmallow import (Schema, fields, validates, ValidationError,
                         post_load, pre_load)
from models import Dataset, Run, Predictor


class AnalysisSchema(Schema):
    """ Primary analysis schema """
    hash_id = fields.Str(dump_only=True, description='Hashed analysis id.')
    parent_id = fields.Str(dump_only=True,
                           description="Parent analysis, if cloned.")

    name = fields.Str(required=True, description='Analysis name.')
    description = fields.Str()
    predictions = fields.Str(description='User apriori predictions.')

    dataset_id = fields.Int(required=True)
    task_name = fields.Str(description='Task name', dump_only=True)
    TR = fields.Float(description='Time repetition (s)', dump_only=True)

    model = fields.Dict(description='BIDS model.')

    created_at = fields.Time(dump_only=True)
    modified_at = fields.Time(dump_only=True)
    submitted_at = fields.Time(
        description='Timestamp of when analysis was submitted for compilation',
        dump_only=True)
    status = fields.Str(
        description='PASSED, FAILED, PENDING, or DRAFT.', dump_only=True)
    locked = fields.Bool(
        description='Is analysis locked by admins?', dump_only=True)
    compile_traceback = fields.Str(
        description='Traceback of compilation error.', dump_only=True)

    private = fields.Bool(description='Analysis private or discoverable?')

    predictors = fields.Nested(
        'PredictorSchema', many=True, only='id',
        description='Predictor id(s) associated with analysis')

    runs = fields.Nested(
        'RunSchema', many=True, only='id',
        description='Runs associated with analysis')

    @validates('dataset_id')
    def validate_dsid(self, value):
        if Dataset.query.filter_by(id=value).count() == 0:
            raise ValidationError('Invalid dataset id.')

    @validates('runs')
    def validate_runs(self, value):
        try:
            [Run.query.filter_by(**r).one() for r in value]
        except:
            raise ValidationError('Invalid run id!')

    @validates('predictors')
    def validate_preds(self, value):
        try:
            [Predictor.query.filter_by(**r).one() for r in value]
        except:
            raise ValidationError('Invalid predictor id.')

    @pre_load
    def unflatten(self, in_data):
        if 'runs' in in_data:
            in_data['runs'] = [{"id": r} for r in in_data['runs']]
        if 'predictors' in in_data:
            in_data['predictors'] = [{"id": r} for r in in_data['predictors']]

        return in_data

    @post_load
    def nested_object(self, args):
        if 'runs' in args:
            args['runs'] = [
                Run.query.filter_by(**r).one() for r in args['runs']]

        if 'predictors' in args:
            args['predictors'] = [
                Predictor.query.filter_by(**r).one()
                for r in args['predictors']]

        return args

    class Meta:
        strict = True


class AnalysisFullSchema(AnalysisSchema):
    """ Analysis schema, with additional nested fields """
    runs = fields.Nested(
        'RunSchema', many=True, description='Runs associated with analysis',
        exclude=['dataset_id', 'task'], dump_only=True)

    predictors = fields.Nested(
        'PredictorSchema', many=True, only=['id', 'name'],
        description='Predictor id(s) associated with analysis', dump_only=True)


class AnalysisResourcesSchema(Schema):
    """ Schema for Analysis resources. """
    preproc_address = fields.Nested(
        'DatasetSchema', only='preproc_address', attribute='dataset')
    dataset_address = fields.Nested(
        'DatasetSchema', only='dataset_address', attribute='dataset')
    dataset_name = fields.Nested(
        'DatasetSchema', only='name', attribute='dataset')


class AnalysisCompiledSchema(Schema):
    """ Simple route for checking if analysis compilation status. """
    status = fields.Str(description='PASSED, FAILED, PENDING, or DRAFT.',
                        dump_only=True)
    compile_traceback = fields.Str(
        description='Traceback of compilation error.')


class ReportSchema(Schema):
    """ Schema for report results """
    generated_at = fields.Time(description='Time report was generated')
    result = fields.Dict(description='Links to report resources')
    status = fields.Str(description='Report status')
    traceback = fields.Str(
        description='Traceback of generation error.')
