from marshmallow import fields, post_dump, Schema


class ExtractedFeatureSchema(Schema):
    id = fields.Int(description="Extractor id")
    description = fields.Str(description="Feature description.")
    created_at = fields.Str(description="Extraction timestamp.")
    extractor_name = fields.Str(description="Extractor name.")
    modality = fields.Str()


class PredictorSchema(Schema):
    id = fields.Int()
    name = fields.Str(description="Predictor name.")
    description = fields.Str(description="Predictor description")
    extracted_feature = fields.Nested('ExtractedFeatureSchema', skip_if=None)
    source = fields.Str()

    max = fields.Float(description="Maximum value")
    min = fields.Float(description="Minimum value")
    mean = fields.Float(description="Mean value")
    stddev = fields.Float(description="Standard deviation of value")
    num_na = fields.Int(description="Number of missing values")
    dataset_id = fields.Int()

    @post_dump
    def remove_null_values(self, data):
        if data.get('extracted_feature', True) is None:
            data.pop('extracted_feature')
        return data


class PredictorRunSchema(Schema):
    run_id = fields.Int()
    mean = fields.Number()
    stdev = fields.Number()


class PredictorCollectionSchema(Schema):
    """ Schema for report results """
    id = fields.Int(description='Collection id')
    uploaded_at = fields.Time(description='Time images upload began')
    # predictor_id = fields.Dict(description='NeuroVault collection id')
    status = fields.Str(description='Upload status')
    traceback = fields.Str(description='Traceback of error.')
    collection_name = fields.Str(description='Name of collection')
    predictors = fields.Nested(
        'PredictorSchema', only=['id', 'name', 'private', 'dataset_id'],
        many=True)
