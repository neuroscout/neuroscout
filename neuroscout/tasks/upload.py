import pandas as pd
from pynv import Client
import re
from pathlib import Path

from ..utils.db import get_or_create
from ..database import db
from ..models import (
    Predictor, PredictorCollection, PredictorEvent, PredictorRun,
    NeurovaultFileUpload)

from .utils.io import update_record


def upload_collection(flask_app, filenames, runs, dataset_id, collection_id,
                      descriptions=None, cache=None):
    """ Create new Predictors from TSV files
    Args:
        filenames list of (str): List of paths to TSVs
        runs list of (int): List of run ids to apply events to
        dataset_id (int): Dataset id.
        collection_id (int): Id of collection object
        descriptions (dict): Optional descriptions for each column
        cache (obj): Optional flask cache object
    """
    if cache is None:
        from ..core import cache as cache
    if descriptions is None:
        descriptions = {}

    collection_object = PredictorCollection.query.filter_by(
        id=collection_id).one()

    # Load into pandas
    try:
        events = [pd.read_csv(f, sep='\t') for f in filenames]
    except Exception as e:
        update_record(
            collection_object,
            exception=e,
            traceback='Error reading event files'
        )
        raise

    # Check columns are all the same across all files
    cols = [set(e.columns) for e in events]
    common_cols = set.intersection(*cols)
    if not len(common_cols) == len(cols[0]):
        update_record(
            collection_object,
            traceback='Event files contain distinct columns'
        )
        raise Exception('Event files contain distinct columns')

    if not set(['onset', 'duration']).issubset(common_cols):
        update_record(
            collection_object,
            traceback='Not all columns have "onset" and "duration"'
        )
        raise Exception('Not all columns have "onset" and "duration"')

    pe_objects = []
    try:
        for col in common_cols - set(['onset', 'duration']):
            predictor = Predictor(
                name=col,
                source=f'Collection: {collection_object.collection_name}',
                dataset_id=dataset_id,
                predictor_collection_id=collection_object.id,
                private=True,
                description=descriptions.get(col))
            db.session.add(predictor)
            db.session.commit()

            for ix, e in enumerate(events):
                select = e[['onset', 'duration', col]].dropna()
                for run_id in runs[ix]:
                    # Add PredictorRun
                    pr, _ = get_or_create(
                        PredictorRun, predictor_id=predictor.id, run_id=run_id)
                    for _, row in select.iterrows():
                        row = row.to_dict()
                        pe_objects.append(
                            PredictorEvent(
                                predictor_id=predictor.id,
                                run_id=run_id, onset=row['onset'],
                                duration=row['duration'], value=row[col])
                            )
            collection_object.predictors.append(predictor)

        db.session.bulk_save_objects(pe_objects)
        db.session.commit()
    except Exception as e:
        cache.clear()
        db.session.rollback()
        update_record(
            collection_object,
            exception=e,
            traceback=f'Error creating predictors. Failed processing {col}'
        )
        raise

    cache.clear()
    return update_record(
        collection_object,
        status='OK'
    )


MAP_TYPE_CHOICES = {
    't': 'T',
    'p': 'P',
    'effect': 'U',
    'variance': 'V',
}


def upload_neurovault(flask_app, file_id, n_subjects=None):
    """ Upload image file to NeuroVault
    Args:
        file_id (int): NeurovaultFileUpload object id
        n_subjects (int): Number of subjects in analysis
    """
    api = Client(access_token=flask_app.config['NEUROVAULT_ACCESS_TOKEN'])
    file_object = NeurovaultFileUpload.query.filter_by(id=file_id).one()
    path = Path(file_object.path)

    new_p = Path(str(path).replace('space-MNI152NLin2009cAsym_', ''))
    path.rename(new_p)

    basename = new_p.parts[-1]

    contrast_name = re.findall('contrast-(.*)_', str(basename))[0]
    map_type = re.findall('stat-(.*)_', str(basename))[0]
    map_type = MAP_TYPE_CHOICES[map_type]

    if file_object.level == 'GROUP':
        analysis_level = 'G'
    else:
        analysis_level = 'S'
        n_subjects = None

    try:
        api.add_image(
            file_object.collection.collection_id, str(new_p),
            name=contrast_name,
            modality="fMRI-BOLD", map_type=map_type,
            analysis_level=analysis_level, cognitive_paradigm_cogatlas='None',
            number_of_subjects=n_subjects, is_valid=True)
    except Exception as e:
        update_record(
            file_object,
            exception=e,
            traceback='Error adding image to collection'
        )
        raise

    return update_record(
        file_object,
        status='OK'
        )
