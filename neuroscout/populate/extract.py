""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from ..core import cache
from ..database import db
from .utils import tqdm_joblib
import socket

from pathlib import Path
from tqdm import tqdm
from joblib import Parallel, delayed, parallel_backend
from ..utils.db import get_or_create

from pliers.stimuli import load_stims, ComplexTextStim, TextStim
from pliers.graph import Graph
from ..models import (
    Dataset, Task, Predictor, PredictorRun, Run, Stimulus,
    RunStimulus, ExtractedFeature, ExtractedEvent)
from .annotate import FeatureSerializer

socket.setdefaulttimeout(10000)


def _load_stim(stim_model):
    stims = []
    if stim_model.path is None:
        stims.append(
            (stim_model, ComplexTextStim(text=stim_model.content)))
        stims.append(
            (stim_model, TextStim(text=stims[-1][1].data)))

    else:
        stims.append(
            (stim_model, load_stims(stim_model.path)))
    return stims


def _query_stim_models(dataset_name, task_name=None, graphs=None):
    """ Given a dataset and task, query all matching stimuli.
    Optionally a list of graphs can be provided which further restrict
    the stimuli to only those necessary for those graphs """

    stim_models = Stimulus.query.filter_by(active=True).filter(
        Stimulus.mimetype != 'text/csv')

    # Determine the necessary stimuli to load
    if graphs is not None:
        mimetypes = []
        for g in graphs:
            it = g.roots[0].transformer._input_type
            if not isinstance(list, it):
                it = list([it])
            for i in it:
                mimetypes.append(str(i).split('.')[-2])
        stim_models = stim_models.filter(
            Stimulus.mimetype.op('~')('|'.join(mimetypes)))

    stim_models = stim_models.join(RunStimulus).join(Run).join(Task)

    if task_name is not None:
        stim_models = stim_models.filter_by(name=task_name)

    stim_models = stim_models.join(Dataset).filter_by(name=dataset_name)

    return stim_models.all()


def _extract(graphs, stim_object):
    """ For a stim_object, load stim and apply graphs """
    results = []
    for stim_obj, pliers_stim in _load_stim(stim_object):
        # For each graph, check compatability, and then extract
        for graph in graphs:
            ext = graph.roots[0].transformer
            if ext._stim_matches_input_types(pliers_stim):
                # Hacky workaround. Look for compatible AVI
                if 'GoogleVideoAPIShotDetectionExtractor' in str(ext.__class__):
                    pliers_stim.filename = str(
                        Path(pliers_stim.filename).with_suffix('.avi'))
                res = graph.transform(pliers_stim, merge=False)[0]
                results.append((stim_obj.id, res))
    del pliers_stim
    return results


def _create_efs(results, **serializer_kwargs):
    """ Create ExtractedFeature models from Pliers results.
        Only creates one object per unique feature
    Args:
        results - list of zipped pairs of Stimulus objects and ExtractedResult
                  objects
        serializer_kwargs - kwargs for Feature serialization
    Returns:
        ext_feats - dictionary of hash of ExtractedFeatures to EF objects
    """
    ext_feats = {}
    serializer = FeatureSerializer(**serializer_kwargs)
    bulk_ees = []

    print("Creating ExtractedFeatures...")
    for stim_id, result in tqdm(results):
        for ee_props, ef_props in serializer.load(result):
            # Hash extractor name + feaFture name
            feat_hash = ef_props['sha1_hash']

            # If we haven't already added this feature
            if feat_hash not in ext_feats:
                # Create/get feature
                ef_model = ExtractedFeature(**ef_props)
                db.session.add(ef_model)
                db.session.commit()
                ext_feats[feat_hash] = ef_model

            # Create ExtractedEvents
            bulk_ees.append(
                dict(stimulus_id=stim_id,
                     ef_id=ext_feats[feat_hash].id,
                     **ee_props))
    db.session.execute(ExtractedEvent.__table__.insert(), bulk_ees)
    db.session.commit()

    return ext_feats


def create_predictors(features, dataset_name, task_name=None, run_ids=None,
                      percentage_include=.9, clear_cache=True):
    """ Create Predictors from Extracted Features.
        Args:
            features (object) - ExtractedFeature objects
            dataset_name (str) - Dataset name
            task_name (str) - Task name
            run_ids (list of ints) - Optional list of run_ids for which to
                                     create PredictorRun for.
            clear_cache (bool) - Clear API cache
    """
    print("Creating predictors")

    if clear_cache:
        cache.clear()

    dataset = Dataset.query.filter_by(name=dataset_name).one()

    if task_name is not None:
        task = Task.query.filter_by(
            dataset_id=dataset.id).filter_by(name=task_name).one()
        n_runs = len(task.runs)
    else:
        n_runs = len(dataset.runs)

    # Create/Get Predictors
    all_preds = []
    for ef in features:
        # Calculate num of runs this feature is present in
        unique_runs = RunStimulus.query.filter(
            RunStimulus.stimulus_id.in_(
                set([ee.stimulus_id for ee in ef.extracted_events]))).\
                distinct('run_id')

        if unique_runs.count() / n_runs > percentage_include:
            all_preds.append(get_or_create(
                Predictor, name=ef.feature_name, description=ef.description,
                dataset_id=dataset.id,
                source='extracted', ef_id=ef.id)[0])

    # Create PredictorRuns
    for ix, predictor in enumerate(tqdm(all_preds)):
        ef = features[ix]
        all_rs = []
        # For all instances for stimuli in this set of runs
        for ee in ef.extracted_events:
            query = RunStimulus.query.filter_by(stimulus_id=ee.stimulus_id)
            if run_ids is not None:
                query = query.filter(RunStimulus.run_id.in_(run_ids))
            all_rs += [(predictor.id, rs.run_id) for rs in query]

        all_rs = [dict(predictor_id=pred_id, run_id=run_id)
                  for pred_id, run_id in set(all_rs)]
        db.session.execute(PredictorRun.__table__.insert(), all_rs)
        db.session.commit()

    return [p.id for p in all_preds]


def extract_features(graphs, dataset_name=None, task_name=None, n_jobs=1,
                     **serializer_kwargs):
    """ Extract features using pliers for a dataset/task
        Args:
            graphs - List of Graphs to apply to stimuli
            dataset_name - dataset name
            task_name - task name (optional)
            serializer_kwargs - Arguments to pass to FeatureSerializer
        Output:
            list of db ids of extracted features
    """
    # If no dataset is specific extract for all datasets recursively
    if dataset_name is None:
        return [extract_features(
            graphs, dataset.name, None, **serializer_kwargs)
                for dataset in Dataset.query.filter_by(active=True)]
    else:
        # Load Pliers Graph objects
        graphs = [Graph(g) for g in graphs]

        stims = _query_stim_models(
            dataset_name, task_name, graphs=graphs)

        # Apply graphs to each stim_object in parallel
        with parallel_backend('multiprocessing'):
            with tqdm_joblib(tqdm(desc="Extracting...", total=len(stims))):
                results = Parallel(
                    n_jobs=n_jobs)(delayed(_extract)(graphs, s) for s in stims)

        # Flatten
        results = [item for sublist in results for item in sublist]

        ext_feats = _create_efs(results, **serializer_kwargs)

        return create_predictors(
            [ef for ef in ext_feats.values() if ef.active],
            dataset_name, task_name)


def _load_complex_text_stim_models(dataset_name, task_name):
    """ Reconstruct ComplexTextStim object of complete run transcript
    for each run in a task """
    stim_models = Stimulus.query.filter_by(
        active=True, mimetype='text/csv').join(
            RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    stims = []
    print("Loading stim models...")
    for stim_model in tqdm(stim_models):
        # Reconstruct complete ComplexTextStim
        rs_transcript = stim_model.run_stimuli.first()
        run_words = Stimulus.query.filter_by(
            mimetype='text/plain').join(RunStimulus).filter_by(
                run_id=rs_transcript.run_id)

        word_stims = []
        for w in run_words:
            for w_rs in w.run_stimuli.filter_by(run_id=rs_transcript.run_id):
                word_stims.append(
                    TextStim(
                        text=w.content, onset=w_rs.onset-rs_transcript.onset,
                        duration=w_rs.duration)
                    )
        word_stims = sorted(word_stims, key=lambda x: x.onset)
        stims.append((stim_model, ComplexTextStim(elements=word_stims)))

    return stims


def _window_stim(cts, n):
    """ Return windowed slices from a ComplexTextStim
        Args:
            cts - _load_complex_text_stim_models
            n - size of window prior to current stimulus
        Output:
            list of ComplexTextStim with n elements
    """
    ix_high = n
    ix_low = 0
    slices = []
    while ix_high <= len(cts.elements):
        subset_stim = ComplexTextStim(elements=cts.elements[ix_low:ix_high])
        slices.append(subset_stim)
        ix_high += 1
        ix_low = ix_high - n
    return slices


def extract_tokenized_features(dataset_name, task_name, extractors):
    """ Extract features that require a ComplexTextStim to give context to
    individual words within a run """
    stims = _load_complex_text_stim_models(dataset_name, task_name)

    results = []
    # For every extractor, extract from complex stims
    for graph, cts_params in extractors:
        print("Graph: {}".format(graph))
        g = Graph(nodes=graph)
        window = cts_params.get("window", "transcript")
        window_n = cts_params.get("n", 25) if window == "pre" else None

        for node in g.nodes.values():
            setattr(node.transformer, "window_method", window)
            if window_n:
                setattr(node.transformer, "window_n", window_n)
        for sm, s in tqdm(stims):
            if window == "transcript":
                # In complete transcript window, save all results
                results += [(sm, res) for res in g.transform(s, merge=False)]
            elif window == "pre":
                for sli in _window_stim(s, window_n):
                    for r in g.transform(sli, merge=False):
                        results.append((sm, r))

    # These results may not be fully recoverable
    # _to_csv(results, dataset_name, task_name)
    object_id = 'max' if window == 'pre' else None
    ext_feats = _create_efs(
        results, object_id=object_id, splat=True, add_all=False, round_n=4)

    return create_predictors([ef for ef in ext_feats.values() if ef.active],
                             dataset_name, task_name)
