"""" Custom transformations of extracted features """
from models import (Dataset, ExtractedFeature, ExtractedEvent,
                    Stimulus, RunStimulus, Run, Task)
from database import db
from sqlalchemy import func
from .utils import hash_data
from .extract import create_predictors

class Postprocessing(object):
    """ Functions applied to one or more ExtractedFeatures """
    @staticmethod
    def num_objects(ef):
        """ Counts the number of Extracted Events for each stimulus """
        ef = ef.one()
        counts = []
        for stimulus_id, count in db.session.query(
            ExtractedEvent.stimulus_id, func.count(
                ExtractedEvent.stimulus_id)).group_by(
                    ExtractedEvent.stimulus_id).filter_by(ef_id=ef.id):
                    counts.append(
                        {'stimulus_id': stimulus_id,
                         'value': count}
                    )

        return counts


def transform_feature(function, new_name, dataset_name,
                         task_name=None, **kwargs):
    # Query to get matching EFs
    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id
    efs =  ExtractedFeature.query.filter_by(**kwargs).join(
            ExtractedEvent).join(Stimulus).filter_by(dataset_id=dataset_id)

    if task_name is not None:
        efs = efs.join(RunStimulus).join(Run).join(Task).filter_by(name=task_name)

    # Apply function and get new values
    ee_results = getattr(Postprocessing, function)(efs)

    ext_name = efs.first().extractor_name
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
