import pandas as pd
from pynv import Client
import tarfile
import re
from tempfile import mkdtemp
from pathlib import Path

from ..utils.db import get_or_create
from ..database import db
from ..models import (
    Predictor, PredictorCollection, PredictorEvent, PredictorRun,
    NeurovaultCollection)

from .utils import update_record


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


def upload_neurovault(flask_app, img_tarball, hash_id, upload_id,
                      timestamp=None, n_subjects=None):
    """ Upload results to NeuroVault
    Args:
        img_tarball (str): tarball path containg images
        hash_id (str): Analysis hash_id
        upload_id (int): NeurovaultCollection object id
        timestamp (str): Current server timestamp
        n_subjects (int): Number of subjects in analysis
    """
    upload_object = NeurovaultCollection.query.filter_by(id=upload_id).one()
    timestamp = "_" + timestamp if timestamp is not None else ''
    api = Client(access_token=flask_app.config['NEUROVAULT_ACCESS_TOKEN'])

    try:
        # Untar:
        tmp_dir = Path(mkdtemp())
        with tarfile.open(img_tarball, mode="r:gz") as tf:
            tf.extractall(tmp_dir)
    except Exception as e:
        update_record(
            upload_object,
            exception=e,
            traceback='Error decompressing image bundle'
        )
        raise

    try:
        collection = api.create_collection(
            '{}{}'.format(hash_id, timestamp))

        for img_path in tmp_dir.glob('*stat-t_statmap.nii.gz'):
            contrast_name = re.findall('contrast-(.*)_', str(img_path))[0]
            api.add_image(
                collection['id'], img_path, name=contrast_name,
                modality="fMRI-BOLD", map_type='T',
                analysis_level='G', cognitive_paradigm_cogatlas='None',
                number_of_subjects=n_subjects, is_valid=True)
    except Exception as e:
        update_record(
            upload_object,
            exception=e,
            traceback='Error uploading, perhaps a \
                collection with the same name exists?'
        )
        raise

    return update_record(
        upload_object,
        collection_id=collection['id'],
        status='OK'
        )
