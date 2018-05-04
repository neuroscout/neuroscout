"""" Custom transformations of extracted features """
from models import (Dataset, ExtractedFeature, ExtractedEvent,
                    Stimulus, RunStimulus, Run, Task)
from database import db
from sqlalchemy import func
from sqlalchemy.sql.expression import cast
from .utils import hash_data
from .extract import create_predictors

class Postprocessing(object):
    """ Functions applied to one or more ExtractedFeatures """
    @staticmethod
    def num_objects(efs, threshold=None):
        """ Counts the number of Extracted Events for each stimulus.
            efs - BaseQuery object with ExtractedFeature object(s)
            threshold - filter threshold for ExtractedEvent value """
        query = db.session.query(
            ExtractedEvent.stimulus_id, func.count(ExtractedEvent.stimulus_id))

        if threshold is not None:
            query = query.filter(cast(ExtractedEvent.value, db.Float) > threshold)

        # Group by stimulus and filter by EFs
        query = query.group_by(
            ExtractedEvent.stimulus_id).filter(
                ExtractedEvent.ef_id.in_(efs.values('id')))

        counts = [{'stimulus_id': stimulus_id, 'value': count}
                  for stimulus_id, count in query]

        return counts



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
    ee_results = getattr(Postprocessing, function)(efs, **func_args)

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
