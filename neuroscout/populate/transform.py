"""" Custom transformations of extracted features """
from models import (Dataset, ExtractedFeature, ExtractedEvent,
                    Stimulus, RunStimulus, Run, Task)
from database import db
from sqlalchemy import func
from .utils import hash_data
from .extract import create_predictors
import pandas as pd

class Postprocessing(object):
    """ Functions applied to one or more ExtractedFeatures """
    def _load_df(self, efs):
        query = ExtractedEvent.query.filter(
            ExtractedEvent.ef_id.in_(efs.values('id')))
        df = pd.read_sql(query.statement, db.session.bind)

        return df

    def num_objects(self, efs, threshold=None):
        """ Counts the number of Extracted Events for each stimulus.
            Args:
                efs - BaseQuery object with ExtractedFeature object(s)
                threshold - filter threshold for ExtractedEvent value
        """
        df = self._load_df(efs)
        if threshold is not None:
            df.value = df.value.astype('float')
            df = df[df.value > threshold]

        counts = df.groupby('stimulus_id').count()['value'].reset_index()

        return counts.to_dict('index').values()

    def dummy(self, efs):
        """ Gives a dummy feature of 1s for each stimulus """
        df = self._load_df(efs)

        dummy = df.groupby('stimulus_id').apply(lambda x: 1).reset_index()
        return dummy.rename(columns={0: 'value'}).to_dict('index').values()


def transform_feature(function, new_name, dataset_name,
                      task_name=None, func_args={}, **kwargs):
    # Query to get latest matching EFs
    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id
    ef_ids = db.session.query(func.max(ExtractedFeature.id)).join(
            ExtractedEvent).join(Stimulus).filter_by(dataset_id=dataset_id)

    if task_name is not None:
        ef_ids = ef_ids.join(
            RunStimulus).join(Run).join(Task).filter_by(name=task_name)

    ef_ids = ef_ids.group_by(ExtractedFeature.feature_name)

    efs =  ExtractedFeature.query.filter(ExtractedFeature.id.in_(
        ef_ids)).filter_by(**kwargs)

    # Apply function and get new values
    ee_results = getattr(Postprocessing(), function)(efs, **func_args)

    ext_name = efs.first().extractor_name + "_trans"
    new_ef = ExtractedFeature(extractor_name=ext_name,
                              feature_name=new_name,
                              active=True,
                              sha1_hash=hash_data(ext_name + new_name)
                              )
    db.session.add(new_ef)
    db.session.commit()

    # Create EEs and predictor
    db.session.bulk_save_objects(
        [ExtractedEvent(ef_id=new_ef.id, **ee) for ee in ee_results]
        )
    db.session.commit()

    create_predictors([new_ef], dataset_id)

    return new_ef.id
