import tarfile
import json
import re
from tempfile import mkdtemp
from pathlib import Path
from app import celery_app
from nistats.reporting import plot_design_matrix
from fitlins.viz import plot_corr_matrix, plot_contrast_matrix
from .compile import build_analysis, plot_save, PathBuilder, impute_confounds
from celery.utils.log import get_task_logger
from pynv import Client

logger = get_task_logger(__name__)


@celery_app.task(name='workflow.compile')
def compile(analysis, predictor_events, resources, bids_dir, run_ids,
            build=False):
    tmp_dir, bundle_paths, _ = build_analysis(
        analysis, predictor_events, bids_dir, run_ids, build=build)

    sidecar = {"RepetitionTime": analysis['TR']}
    # Write out JSON files
    for obj, name in [
      (analysis, 'analysis'),
      (resources, 'resources'),
      (analysis.get('model'), 'model'),
      (sidecar, 'task-{}_bold'.format(analysis['task_name']))]:

        path = (tmp_dir / name).with_suffix('.json')
        json.dump(obj, path.open('w'))
        bundle_paths.append((path.as_posix(), path.name))

    # Save bundle as tarball
    bundle_path = '/file-data/analyses/{}_bundle.tar.gz'.format(
        analysis['hash_id'])
    with tarfile.open(bundle_path, "w:gz") as tar:
        for path, arcname in bundle_paths:
            tar.add(path, arcname=arcname)

    return {'bundle_path': bundle_path}


@celery_app.task(name='workflow.generate_report')
def generate_report(analysis, predictor_events, bids_dir, run_ids, domain):
    _, _, bids_analysis = build_analysis(
        analysis, predictor_events, bids_dir, run_ids)
    outdir = Path('/file-data/reports') / analysis['hash_id']
    outdir.mkdir(exist_ok=True)

    first = bids_analysis.steps[0]
    results = {'design_matrix': [],
               'design_matrix_plot': [],
               'design_matrix_corrplot': [],
               'contrast_plot': []}

    for dm in first.get_design_matrix(
      mode='dense', force=True, entities=False):
        dense = impute_confounds(dm.dense)

        builder = PathBuilder(outdir, domain, analysis['hash_id'], dm.entities)
        # Writeout design matrix
        out, url = builder.build('design_matrix', 'tsv')
        results['design_matrix'].append(url)
        dense.to_csv(out, index=False)

        out, url = builder.build('design_matrix_plot', 'png')
        results['design_matrix_plot'].append(url)
        plot_save(dense, plot_design_matrix, out)

        out, url = builder.build('design_matrix_corrplot', 'png')
        results['design_matrix_corrplot'].append(url)
        plot_save(
            dense.corr(), plot_corr_matrix, out, n_evs=None, partial=None)

    for cm in first.get_contrasts():
        builder = PathBuilder(outdir, domain, analysis['hash_id'],
                              cm[0].entities)
        out, url = builder.build('contrast_matrix', 'png')
        plot_save(cm[0].weights, plot_contrast_matrix, out)
        results['contrast_plot'].append(url)

    return results


@celery_app.task(name='neurovault.upload')
def upload(img_tarball, hash_id, access_token):
    tmp_dir = Path(mkdtemp())
    # Untar:
    with tarfile.open(img_tarball) as tf:
        tf.extractall(tmp_dir)

    api = Client(access_token=access_token)
    collection = api.create_collection(hash_id)

    for img_path in tmp_dir.glob('*.nii.gz'):
        contrast_name = re.findall('contrast-(.*)_', img_path)[0]
        api.add_image(
            collection['id'], img_path, name=contrast_name,
            modality="fMRI-BOLD", map_type='T')
