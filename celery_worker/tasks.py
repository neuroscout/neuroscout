import tarfile
import re
from tempfile import mkdtemp
from pathlib import Path
from celery.utils.log import get_task_logger
from pynv import Client
from hashids import Hashids
import pandas as pd

from neuroscout.basic import create_app
from neuroscout.models import (
    Analysis, Report, NeurovaultCollection, Predictor, PredictorCollection,
    PredictorEvent, PredictorRun)
from neuroscout.utils.db import get_or_create
from neuroscout.database import db

from app import celery_app
from compile import build_analysis, PathBuilder, impute_confounds
from viz import plot_design_matrix, plot_corr_matrix, sort_dm
from utils import update_record, write_jsons, write_tarball, dump_analysis

logger = get_task_logger(__name__)
FILE_DATA = Path('/file-data/')

# Push db context
flask_app = create_app()
flask_app.app_context().push()


@celery_app.task(name='workflow.compile')
def compile(hash_id, run_ids=None, build=False):
    """ Compile analysis_id. Validate analysis using pybids and
    writout analysis bundle
    Args:
        hash_id (str): analysis hash_id
        run_ids (list): Optional list of runs to include
        build (bool): Validate in pybids?
    """
    try:
        analysis_object = Analysis.query.filter_by(hash_id=hash_id).one()
    except Exception as e:
        return {
            'traceback': f'Error loading {hash_id} from db /n {str(e)}'
            }
    try:
        a_id, analysis, resources, predictor_events, bids_dir = dump_analysis(
            hash_id)
    except Exception as e:
        update_record(
            analysis_object,
            exception=e,
            traceback='Error deserializing analysis'
        )
        raise
    try:
        tmp_dir, bundle_paths, _ = build_analysis(
            analysis, predictor_events, bids_dir, run_ids, build=build)
    except Exception as e:
        update_record(
            analysis_object,
            exception=e,
            traceback='Error validating analysis'
        )
        raise

    try:
        sidecar = {'RepetitionTime': analysis['TR']}
        resources['validation_hash'] = Hashids(
            flask_app.config['SECONDARY_HASH_SALT'],
            min_length=10).encode(a_id)

        # Write out JSON files to tmp_dir
        bundle_paths += write_jsons([
                (analysis, 'analysis'),
                (resources, 'resources'),
                (analysis.get('model'), 'model'),
                (sidecar, f'task-{analysis_object.task_name}_bold')
                ], tmp_dir)

        # Save bundle as tarball
        bundle_path = str(
            FILE_DATA / f'analyses/{analysis["hash_id"]}_bundle.tar.gz')
        write_tarball(bundle_paths, bundle_path)
    except Exception as e:
        update_record(
            analysis_object,
            exception=e,
            traceback='Error writing tarball bundle'
        )
        raise

    return update_record(
        analysis_object,
        status='PASSED',
        bundle_path=bundle_path
    )


@celery_app.task(name='workflow.generate_report')
def generate_report(hash_id, report_id, run_ids, sampling_rate, scale):
    """ Generate report for analysis
    Args:
        hash_id (str): analysis hash_id
        report_id (int): Report object id
        run_ids (list): List of run ids
        sampling_rate (float): Rate to re-sample design matrix in Hz
        scale (bool): Scale columns in dm plot
    """
    try:
        report_object = Report.query.filter_by(id=report_id).one()
    except Exception as e:
        return {
            'traceback': f'Error loading {report_id} from db /n {str(e)}'
            }

    domain = flask_app.config['SERVER_NAME']

    try:
        a_id, analysis, resources, predictor_events, bids_dir = dump_analysis(
            hash_id)
    except Exception as e:
        update_record(
            report_object,
            exception=e,
            traceback='Error deserializing analysis'
        )
        raise

    try:
        _, _, bids_analysis = build_analysis(
            analysis, predictor_events, bids_dir, run_ids)
    except Exception as e:
        # Todo: In future, could add more messages here
        update_record(
            report_object,
            exception=e,
            traceback='Error validating analysis'
        )
        raise

    try:
        outdir = FILE_DATA / 'reports' / analysis['hash_id']
        outdir.mkdir(exist_ok=True)

        first = bids_analysis.steps[0]
        results = {
            'design_matrix': [],
            'design_matrix_plot': [],
            'design_matrix_corrplot': []
            }

        hrf = [t for t in
               analysis['model']['Steps'][0]['Transformations']
               if t['Name'] == 'Convolve']

        if sampling_rate is None:
            sampling_rate = 'TR'

        for dm in first.get_design_matrix(
          mode='dense', force=True, entities=False,
          sampling_rate=sampling_rate):
            dense = impute_confounds(dm.dense)
            if hrf:
                dense = sort_dm(dense, interest=hrf[0]['Input'])

            builder = PathBuilder(
                outdir, domain, analysis['hash_id'], dm.entities)
            # Writeout design matrix
            out, url = builder.build('design_matrix', 'tsv')
            results['design_matrix'].append(url)
            dense.to_csv(out, index=False)

            dm_plot = plot_design_matrix(dense, scale=scale)
            results['design_matrix_plot'].append(dm_plot)

            corr_plot = plot_corr_matrix(dense)
            results['design_matrix_corrplot'].append(corr_plot)
    except Exception as e:
        return update_record(
            report_object,
            exception=e,
            traceback='Error generating report outputs'
        )
        raise

    return update_record(
        report_object,
        result=results,
        status='OK'
    )


@celery_app.task(name='neurovault.upload')
def upload(img_tarball, hash_id, upload_id, timestamp=None, n_subjects=None):
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


@celery_app.task(name='collection.upload')
def upload_collection(filenames, runs, dataset_id, collection_id):
    """ Create new Predictors from TSV files
    Args:
        filenames list of (str): List of paths to TSVs
        runs list of (int): List of run ids to apply events to
        dataset_id (int): Dataset id.
        collection_id (int): Id of collection object
    """
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

    try:
        pe_objects = []
        for col in common_cols - set(['onset', 'duration']):
            predictor, _ = get_or_create(
                Predictor, name=col, source='upload', dataset_id=dataset_id)

            for ix, e in enumerate(events):
                for run_id in runs[ix]:
                    # Add PredictorRun
                    pr, _ = get_or_create(
                        PredictorRun, predictor_id=predictor.id, run_id=run_id)
                    for _, row in e.iterrows():
                        pe_objects.append(
                            PredictorEvent(
                                predictor_id=predictor.id,
                                run_id=run_id, onset=row.onset,
                                duration=row.duration, value=row[col])
                            )

            db.session.bulk_save_objects(pe_objects)
            db.session.commit()
    except Exception as e:
        update_record(
            collection_object,
            exception=e,
            traceback=f'Error creating predictors. Failed processing {col}'
        )
        raise

    return update_record(
        collection_object,
        status='OK'
    )
