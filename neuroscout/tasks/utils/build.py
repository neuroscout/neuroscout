import json
import numpy as np
import pandas as pd
from collections import defaultdict
from pathlib import Path
from tempfile import mkdtemp
from bids.analysis import Analysis as BIDSAnalysis
from bids.layout import BIDSLayout
from copy import deepcopy
from celery.utils.log import get_task_logger
from grabbit.extensions.writable import build_path

from ...utils.db import dump_pe
from ...models import Analysis, PredictorEvent, Predictor, RunStimulus
from ...schemas.analysis import AnalysisFullSchema, AnalysisResourcesSchema


PATHS = ['sub-{subject}_[ses-{session}_]task-{task}_[acq-{acquisition}_]'
         '[run-{run}_]events.tsv']
logger = get_task_logger(__name__)


def writeout_events(analysis, pes, outdir):
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
        entities = get_entities(run)
        entities['task'] = analysis['task_name']

        out_cols = {}
        if run_events.empty is False:
            for name, df in run_events.groupby('predictor_id'):
                df_col = df.groupby(['onset', 'duration'])['value'].max()
                df_col = df_col.reset_index().rename(columns={'value': name})
                out_cols[name] = df_col

        # For any columns that don't have events, output n/a file
        for name in set(predictor_names.values()) - out_cols.keys():
            df_col = pd.DataFrame([[0, 0, 'n/a']],
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


def build_analysis(analysis, predictor_events, bids_dir, run_id=None,
                   build=True):
    tmp_dir = Path(mkdtemp())

    entities = [{}]
    if run_id is not None:
        # Get entities of runs, and add to kwargs
        for rid in run_id:
            for run in analysis['runs']:
                if rid == run['id']:
                    entities.append(get_entities(run))
                    break

    entities = merge_dictionaries(*entities)
    entities['scan_length'] = max([r['duration'] for r in analysis['runs']])
    entities['task'] = analysis['task_name']

    # Write out all events
    paths = writeout_events(analysis, predictor_events, tmp_dir)

    if build is False:
        bids_analysis = None
    else:
        # Load events and try applying transformations
        bids_layout = BIDSLayout(bids_dir, derivatives=str(tmp_dir),
                                 validate=False)
        bids_analysis = BIDSAnalysis(
            bids_layout, deepcopy(analysis.get('model')))
        bids_analysis.setup(**entities)

    return tmp_dir, paths, bids_analysis


def create_pes(predictors, run_ids):
    """ Create PredictorEvents from EFs """
    all_pes = []
    for pred in predictors:
        ef = pred.extracted_feature
        # For all instances for stimuli in this task's runs
        for ee in ef.extracted_events:
            # if ee.value:
            query = RunStimulus.query.filter_by(stimulus_id=ee.stimulus_id)
            if run_ids is not None:
                query = query.filter(RunStimulus.run_id.in_(run_ids))
            for rs in query:
                duration = ee.duration
                if duration is None:
                    duration = rs.duration
                all_pes.append(
                    dict(
                        onset=(ee.onset or 0) + rs.onset,
                        value=ee.value,
                        object_id=ee.object_id,
                        duration=duration,
                        predictor_id=pred.id,
                        run_id=rs.run_id,
                        stimulus_id=ee.stimulus_id
                    )
                )
    return all_pes


def dump_analysis(analysis_id, run_id=None):
    """" Serialize analysis and related PredictorEvents to JSON.
    Queries PredictorEvents to get all events for all runs and predictors. """

    # Query for analysis
    analysis = Analysis.query.filter_by(hash_id=analysis_id).one()

    # Dump analysis JSON
    analysis_json = AnalysisFullSchema().dump(analysis)[0]
    resources_json = AnalysisResourcesSchema().dump(analysis)[0]

    # Get run IDs
    all_runs = [r['id'] for r in analysis_json['runs']]
    if run_id is None:
        run_id = all_runs
    if not set(run_id) <= set(all_runs):
        raise ValueError("Incorrect run id specified")

    # Query and dump PredictorEvents
    all_pred_ids = [(p['id']) for p in analysis_json['predictors']]
    all_preds = Predictor.query.filter(Predictor.id.in_(all_pred_ids))

    base_pred_ids = [p.id for p in all_preds.filter_by(ef_id=None)]
    ext_preds = Predictor.query.filter(
        Predictor.id.in_(set(all_pred_ids) - set(base_pred_ids)))

    pes = PredictorEvent.query.filter(
        (PredictorEvent.predictor_id.in_(base_pred_ids)) &
        (PredictorEvent.run_id.in_(run_id)))
    pes = dump_pe(pes)

    pes += create_pes(ext_preds, run_id)

    dataset_path = Path(analysis.dataset.local_path)
    preproc_path = dataset_path / 'derivatives' / 'fmriprep'

    if preproc_path.exists():
        dataset_path = preproc_path
    return (analysis.id, analysis_json, resources_json, pes,
            str(dataset_path))


def get_entities(run):
    """ Get BIDS-entities from run object """
    valid = ['number', 'session', 'subject', 'acquisition']
    entities = {
        r: v
        for r, v in run.items()
        if r in valid and v is not None
        }

    if 'number' in entities:
        entities['run'] = entities.pop('number')
    return entities


def merge_dictionaries(*arg):
    """ Set merge dictionaries """
    dd = defaultdict(set)

    for d in arg:  # you can list as many input dicts as you want here
        for key, value in d.items():
            dd[key].add(value)
    return dict(((k, list(v)) if len(v) > 1 else (k, list(v)[0])
                 for k, v in dd.items()))


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
