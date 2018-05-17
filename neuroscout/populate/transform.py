"""" Custom transformations of extracted features """
from models import (Dataset, ExtractedFeature, ExtractedEvent,
                    Stimulus, RunStimulus, Run, Task)
from app import db
from sqlalchemy import func
from .utils import hash_data
from .extract import create_predictors
import pandas as pd

class Postprocessing(object):
    """ Functions applied to one or more ExtractedFeatures """
    def __init__(self, dataset_name, task_name=None):
        self.dataset_name = dataset_name

        ef_ids = db.session.query(func.max(ExtractedFeature.id)).join(
                ExtractedEvent).join(Stimulus).join(Dataset).filter_by(
                    name=dataset_name)

        if task_name is not None:
            ef_ids = ef_ids.join(
                RunStimulus).join(Run).join(Task).filter_by(name=task_name)

        ef_ids = ef_ids.group_by(ExtractedFeature.feature_name)

        self.efs = ExtractedFeature.query.filter(
            ExtractedFeature.id.in_(ef_ids))

    def _ef_to_df(self, efs):
        query = ExtractedEvent.query.filter(
            ExtractedEvent.ef_id.in_(efs.values('id')))
        return pd.read_sql(query.statement, db.session.bind)

    @staticmethod
    def num_objects(ee_df, threshold=None):
        """ Counts the number of Extracted Events for each stimulus.
            Args:
                ee_df - ExtractedEvents in pandas df format
                threshold - filter threshold for ExtractedEvent value
        """
        if threshold is not None:
            ee_df.value = ee_df.value.astype('float')
            ee_df = ee_df[ee_df.value > threshold]

        counts = ee_df.groupby('stimulus_id').count()['value'].reset_index()

        return counts.to_dict('index').values()

    @staticmethod
    def dummy(ee_df):
        """ Returns a dummy feature of 1s for each stimulus
            Args:
                ee_df - ExtractedEvents in pandas df format
        """
        dummy = ee_df.groupby('stimulus_id').apply(lambda x: 1).reset_index()
        return dummy.rename(columns={0: 'value'}).to_dict('index').values()

    def apply_transformation(self, new_name, function, func_args={}, **filter):
        """ Queries EFs, applies transformation, and saves as new EF/Predictor
        Args:
            new_name - Feature/predictor name for transformed results
            func - Function name to apply
            func_args - keyword args for transformation function
            filter - arguments to filter ExtractedFeatures
        Returns:
            Database id of new ExtractedFeature
        """
        # Query EFs
        efs = self.efs.filter_by(**filter)

        # Create EF
        ext_name = efs.first().extractor_name + "_trans"
        new_ef = ExtractedFeature(
            extractor_name=ext_name, feature_name=new_name,
            active=True, sha1_hash=hash_data(ext_name + new_name))
        db.session.add(new_ef)
        db.session.commit()

        # Apply function, get new EE values, and create models
        ee_results = getattr(self, function)(self._ef_to_df(efs), **func_args)

        # Create EEs and predictor
        db.session.bulk_save_objects(
            [ExtractedEvent(ef_id=new_ef.id, **ee) for ee in ee_results]
            )
        db.session.commit()

        # Create Predictors from EFs
        create_predictors([new_ef], self.dataset_name)

        return new_ef.id
