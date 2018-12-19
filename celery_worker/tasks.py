import tarfile
import json
import pandas as pd
from collections import defaultdict
from pathlib import Path
from tempfile import mkdtemp
from bids.analysis import Analysis
from bids.layout import BIDSLayout
from grabbit.extensions.writable import build_path
from copy import deepcopy
from celery.utils.log import get_task_logger
from app import celery_app
from matplotlib import pyplot as plt
from nistats.reporting import plot_design_matrix
from fitlins.viz import plot_corr_matrix, plot_contrast_matrix

plt.set_cmap('viridis')
logger = get_task_logger(__name__)
PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_[acq-{acquisition}_]'
         '[run-{run}_]events.tsv']
REPORT_PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_'
                '[acq-{acquisition}_][run-{run}_]{type}.{extension}']


def _get_entities(run):
    """ Get BIDS-entities from run object """
    entities = {
        r: v
        for r, v in run.items()
        if r in ['number', 'session', 'subject', 'acquisition'] and v is not None
        }

    if 'number' in entities:
        entities['run'] = entities.pop('number')
    return entities


def _writeout_events(analysis, pes, outdir):
    """ Writeout predictor_events into BIDS event files """
    desc = {
        'Name': analysis['hash_id'],
        'BIDSVersion': '1.1.1',
        'PipelineDescription': {'Name': 'Neuroscout Events'}
        }

    desc_path = (outdir / 'dataset_description.json')
    paths = [(str(desc_path), 'dataset_description.json')]
    json.dump(desc, desc_path.open('w'))

    outdir = outdir / "func"
    outdir.mkdir(exist_ok=True)

    # Load events and rename columns to human-readable
    pes = pd.DataFrame(pes)
    predictor_names = {p['id']: p['name'] for p in analysis['predictors']}
    pes.predictor_id = pes.predictor_id.map(predictor_names)

    # Write out event files
    for run in analysis.get('runs'):
        # Write out event files for each run_id
        run_events = pes[pes.run_id == run['id']].drop('run_id', axis=1)
        entities = _get_entities(run)
        entities['task'] = analysis['task_name']

        if run_events.empty is False:
            for name, df in run_events.groupby('predictor_id'):
                df_col = df.groupby(['onset', 'duration'])['value'].max()
                df_col = df_col.reset_index().rename(columns={'value': name})

                # Write out BIDS path
                fname = outdir / name / build_path(entities, path_patterns=PATHS)
                fname.parent.mkdir(exist_ok=True)
                paths.append(
                    (str(fname), 'events/{}/{}'.format(name, fname.name)))
                df_col.to_csv(fname, sep='\t', index=False)

    return paths


def _merge_dictionaries(*arg):
    """ Set merge dictionaries """
    dd = defaultdict(set)

    for d in arg:  # you can list as many input dicts as you want here
        for key, value in d.items():
            dd[key].add(value)
    return dict(((k, list(v)) if len(v) > 1 else (k, list(v)[0])
                 for k, v in dd.items()))


def _build_analysis(analysis, predictor_events, bids_dir, run_id=None,
                    build=True):
    tmp_dir = Path(mkdtemp())

    entities = [{}]
    if run_id is not None:
        # Get entities of runs, and add to kwargs
        for rid in run_id:
            for run in analysis['runs']:
                if rid == run['id']:
                    entities.append(_get_entities(run))
                    break

    entities = _merge_dictionaries(*entities)
    entities['scan_length'] = max([r['duration'] for r in analysis['runs']])
    entities['task'] = analysis['task_name']

    # Write out all events
    paths = _writeout_events(analysis, predictor_events, tmp_dir)

    if build is False:
        bids_analysis = None
    else:
        # Load events and try applying transformations
        bids_layout = BIDSLayout(bids_dir, derivatives=str(tmp_dir),
                                 validate=False)
        bids_analysis = Analysis(
            bids_layout, deepcopy(analysis.get('model')))
        bids_analysis.setup(**entities)

    return tmp_dir, paths, bids_analysis


@celery_app.task(name='workflow.compile')
def compile(analysis, predictor_events, resources, bids_dir, run_ids,
            build=False):
    tmp_dir, bundle_paths, _ = _build_analysis(
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


def _plot_save(dm, plotter, outfile, **kwargs):
    fig = plt.figure(figsize=(9, 9))
    axes = plt.gca()
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    ax = plotter(dm, ax=axes, **kwargs)
    xtl = ax.get_xticklabels()
    ax.set_xticklabels(xtl, rotation=90, fontsize=10)
    fig.savefig(outfile, bbox_inches='tight')
    plt.close(fig)


class PathBuilder():
    def __init__(self, outdir, domain, hash, entities):
        self.outdir = outdir
        self.domain = domain
        self.hash = hash
        self.entities = entities

    def build(self, type, extension):
        file = build_path(
            {**self.entities, 'type': type, 'extension': extension},
            path_patterns=REPORT_PATHS)
        outfile = str(self.outdir / file)
        return outfile, '{}/reports/{}/{}'.format(self.domain, self.hash, file)


@celery_app.task(name='workflow.generate_report')
def generate_report(analysis, predictor_events, bids_dir, run_ids, domain):
    _, _, bids_analysis = _build_analysis(
        analysis, predictor_events, bids_dir, run_ids)
    outdir = Path('/file-data/reports') / analysis['hash_id']
    outdir.mkdir(exist_ok=True)

    first = bids_analysis.steps[0]
    results = {'design_matrix': [],
               'design_matrix_plot': [],
               'design_matrix_corrplot': [],
               'contrast_plot': []}

    for dm in first.get_design_matrix(
      mode='dense', force=True, entities=False, sampling_rate=5):
        builder = PathBuilder(outdir, domain, analysis['hash_id'], dm.entities)
        # Writeout design matrix
        out, url = builder.build('design_matrix', 'tsv')
        results['design_matrix'].append(url)
        dm.dense.to_csv(out, index=False)

        out, url = builder.build('design_matrix_plot', 'png')
        results['design_matrix_plot'].append(url)
        _plot_save(dm.dense, plot_design_matrix, out)

        out, url = builder.build('design_matrix_corrplot', 'png')
        results['design_matrix_corrplot'].append(url)
        _plot_save(
            dm.dense.corr(), plot_corr_matrix, out, n_evs=None, partial=None)

    for cm in first.get_contrasts():
        builder = PathBuilder(outdir, domain, analysis['hash_id'], cm[0].entities)
        out, url = builder.build('contrast_matrix', 'png')
        _plot_save(cm[0].weights, plot_contrast_matrix, out)
        results['contrast_plot'].append(url)

    return results
