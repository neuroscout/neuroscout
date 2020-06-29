from marshmallow import (Schema, fields, validates, ValidationError,
                         post_load, pre_load)
from ..models import Dataset, Run, Predictor
from .dataset import DatasetSchema
from .run import RunSchema
from .predictor import PredictorSchema


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
    locked = fields.Bool(
        description='Is analysis locked by admins?', dump_only=True)
    compile_traceback = fields.Str(
        description='Traceback of compilation error.', dump_only=True)
    status = fields.Str(
        description='PASSED, FAILED, PENDING, or DRAFT.', dump_only=True)
    upload_status = fields.Str(
        description='PASSED, FAILED, PENDING, or DRAFT.', dump_only=True)

    private = fields.Bool(description='Analysis private or discoverable?')

    predictors = fields.Nested(
        PredictorSchema, many=True, only='id',
        description='Predictor id(s) associated with analysis')

    runs = fields.Nested(
        RunSchema, many=True, only='id',
        description='Runs associated with analysis')

    @validates('dataset_id')
    def validate_dsid(self, value):
        if Dataset.query.filter_by(id=value).count() == 0:
            raise ValidationError('Invalid dataset id.')

    @validates('runs')
    def validate_runs(self, value):
        try:
            [Run.query.filter_by(**r).one() for r in value]
        except Exception:
            raise ValidationError('Invalid run id!')

    @validates('predictors')
    def validate_preds(self, value):
        try:
            [Predictor.query.filter_by(**r).one() for r in value]
        except Exception:
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


class AnalysisResourcesSchema(Schema):
    """ Schema for Analysis resources. """
    preproc_address = fields.Nested(
        DatasetSchema, only='preproc_address', attribute='dataset')
    dataset_address = fields.Nested(
        DatasetSchema, only='dataset_address', attribute='dataset')
    dataset_name = fields.Nested(
        DatasetSchema, only='name', attribute='dataset')


class AnalysisCompiledSchema(Schema):
    """ Simple route for checking if analysis compilation status. """
    status = fields.Str(description='PASSED, FAILED, PENDING, or DRAFT.',
                        dump_only=True)
    traceback = fields.Str(
        description='Traceback of compilation error.')


class NeurovaultFileUploadSchema(Schema):
    level = fields.Str(
        description='Image analysis level'
    )
    status = fields.Str(description='Upload status')
    traceback = fields.Str(
        description='Traceback of upload error.')
    basename = fields.Str(description='Basename of file')


class NeurovaultCollectionSchema(Schema):
    """ Schema for report results """
    uploaded_at = fields.Time(description='Time collections was created')
    collection_id = fields.Dict(description='NeuroVault collection id')


class NeurovaultCollectionSchemaStatus(NeurovaultCollectionSchema):
    files = fields.Nested(
        NeurovaultFileUploadSchema, many=True)


class AnalysisFullSchema(AnalysisSchema):
    """ Analysis schema, with additional nested fields """
    runs = fields.Nested(
        RunSchema, many=True, description='Runs associated with analysis',
        exclude=['dataset_id', 'task'], dump_only=True)

    predictors = fields.Nested(
        PredictorSchema, many=True, only=['id', 'name'],
        description='Predictor id(s) associated with analysis', dump_only=True)

    neurovault_collections = fields.Nested(
        NeurovaultCollectionSchema, many=True,
        description="Neurovault Collections of analysis results"
    )


class ReportSchema(Schema):
    """ Schema for report results """
    generated_at = fields.Time(description='Time report was generated')
    result = fields.Dict(description='Links to report resources')
    status = fields.Str(description='Report status')
    scale = fields.Boolean(description='Is plot scaled for display purposes')
    sampling_rate = fields.Float(
        description='Sampling rate to resample design matrix to.')
    warnings = fields.List(
        fields.Str(), description='Report warnings')
    traceback = fields.Str(
        description='Traceback of generation error.')


class BibliographySchema(Schema):
    """ Schema for analysis bibliographies """
    tools = fields.List(
        fields.Str, description='Tools used in the analysis.')
    data = fields.List(
        fields.Str, description='Datasets used in the analysis.')
    extractors = fields.List(
        fields.Str, description='Extractors used in the analysis.')
    csl_json = fields.List(
        fields.Dict, description='CSL-JSON of all references.')
