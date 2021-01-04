import json
import numpy as np
import pandas as pd
from flask import current_app
from pathlib import Path
from tempfile import mkdtemp
from bids.analysis import Analysis as BIDSAnalysis
from bids.layout.index import BIDSLayoutIndexer
from bids.layout import BIDSLayout
from copy import deepcopy
from grabbit.extensions.writable import build_path

PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_[acq-{acquisition}_]'
         '[run-{run}_]events.tsv']


def writeout_events(analysis, pes, outdir, run_ids=None):
    """ Writeout predictor_events into BIDS event files """
    analysis_runs = analysis.get('runs', [])
    if run_ids is not None:
        analysis_runs = [r for r in analysis_runs if r['id'] in run_ids]

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
    for run in analysis_runs:
        # Write out event files for each run_id
        run_events = pes[pes.run_id == run['id']].drop('run_id', axis=1)
        entities = _get_entities(run)

        out_cols = {}
        if run_events.empty is False:
            for name, df in run_events.groupby('predictor_id'):
                df_col = df.groupby(['onset', 'duration'])['value'].max()
                df_col = df_col.reset_index().rename(
                    columns={'value': name})
                out_cols[name] = df_col

        # For any columns that don't have events, output n/a file
        for name in set(predictor_names.values()) - out_cols.keys():
            df_col = pd.DataFrame([[0, 1, 'n/a']],
                                  columns=['onset', 'duration', name])
            out_cols[name] = df_col

        # Write out files
        for name, df_col in out_cols.items():
            # Write out BIDS path
            fname = outdir / name / build_path(
                entities, path_patterns=PATHS)
            fname.parent.mkdir(exist_ok=True)
            paths.append(
                (str(fname), 'events/{}/{}'.format(name, fname.name)))
            df_col.to_csv(fname, sep='\t', index=False)

    return paths


def build_analysis(analysis, predictor_events, bids_dir,
                   run_ids=None, build=True):
    """ Write out and build analysis object """
    tmp_dir = Path(mkdtemp())

    # Get set of entities across analysis
    run_entities = []
    if run_ids is not None:
        for rid in run_ids:
            for run in analysis['runs']:
                if rid == run['id']:
                    run_entities.append(_get_entities(run))
                    break

    scan_length = max([r['duration'] for r in analysis['runs']])

    # Write out all events
    paths = writeout_events(
        analysis, predictor_events, tmp_dir, run_ids)

    if build is False:
        bids_analysis = None
    else:
        bids_layout = _load_cached_layout(
            bids_dir, analysis['dataset_id'])
        bids_layout.add_derivatives(str(tmp_dir))

        bids_analysis = BIDSAnalysis(
            bids_layout, deepcopy(analysis.get('model')))

        if run_entities:
            for ents in run_entities:
                bids_analysis.setup(**ents, scan_length=scan_length)
        else:
            bids_analysis.setup(scan_length=scan_length)

    return tmp_dir, paths, bids_analysis


def _load_cached_layout(bids_dir, dataset_id):
    layout_path = current_app.config['FILE_DIR'] / 'layouts' / \
        f"{dataset_id}"

    if layout_path.exists():
        bids_layout = BIDSLayout.load(str(layout_path))
    else:
        # Load events and try applying transformations
        metadata_filter = {
            'extension': ['nii.gz'],
            'suffix': 'bold',
        }
        indexer = BIDSLayoutIndexer(validate=False, **metadata_filter)
        bids_layout = BIDSLayout(bids_dir, database_path=layout_path,
                                 indexer=indexer)

    return bids_layout


def _get_entities(run, **kwargs):
    """ Get BIDS-entities from run object """
    valid = ['number', 'session', 'subject', 'acquisition', 'task_name']
    entities = {
        r: v
        for r, v in run.items()
        if r in valid and v is not None
        }

    if 'number' in entities:
        entities['run'] = entities.pop('number')

    if 'task_name' in entities:
        entities['task'] = entities.pop('task_name')

    entities = {**entities, **kwargs}

    return entities


def impute_confounds(dense):
    """ Impute first TR for confounds that may have n/as """
    for imputable in ('framewise_displacement', 'std_dvars', 'dvars'):
        if imputable in dense.columns:
            vals = dense[imputable].values
            if not np.isnan(vals[0]):
                continue

            # Impute the mean non-zero, non-NaN value
            dense[imputable][0] = np.nanmean(vals[vals != 0])
    return dense
