""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from flask import current_app
from ..core import cache
from ..database import db
import socket

from pathlib import Path
import datetime
from progressbar import progressbar
from ..utils.db import get_or_create

from pliers.stimuli import load_stims, ComplexTextStim, TextStim
from pliers.extractors import merge_results
from pliers.graph import Graph
from ..models import (
    Dataset, Task, Predictor, PredictorRun, Run, Stimulus,
    RunStimulus, ExtractedFeature, ExtractedEvent)
from .annotate import FeatureSerializer

socket.setdefaulttimeout(10000)


def _load_stim_models(dataset_name, task_name):
    """ Given a dataset and task, load all available stimuli as Pliers
    stimuli, and pair them with original database stim object. """
    stim_models = Stimulus.query.filter_by(active=True).filter(
        Stimulus.mimetype != 'text/csv').join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    stims = []
    print("Loading stim models...")
    for stim_model in progressbar(stim_models):
        if stim_model.path is None:
            stims.append(
                (stim_model, ComplexTextStim(text=stim_model.content)))
            stims.append(
                (stim_model, TextStim(text=stims[-1][1].data)))

        else:
            stims.append(
                (stim_model, load_stims(stim_model.path)))

    return stims


def _extract(graphs, stims):
    """ Apply list of graphs to complete list of stimuli in dataset """
    results = []
    # For every extractor, extract from matching stims
    for g in graphs:
        graph = Graph(g)
        ext = graph.roots[0].transformer
        print("Extractor: {}".format(ext.name))
        valid_stims = []
        for sm, s in stims:
            if ext._stim_matches_input_types(s):
                # Hacky workaround. Look for compatible AVI
                if 'GoogleVideoAPIShotDetectionExtractor' in str(ext.__class__):
                    s.filename = str(Path(s.filename).with_suffix('.avi'))
                valid_stims.append((sm, s))
        results += [(sm, graph.transform(s, merge=False)[0])
                    for sm, s in progressbar(valid_stims)]
    return results


def _to_csv(results, dataset_name, task_name):
    """ Save extracted Pliers results to file. """
    if results != [] and 'EXTRACTION_DIR' in current_app.config:
        results_df = merge_results(list(zip(*results))[1])
        outfile = Path(
            current_app.config['EXTRACTION_DIR']) / '{}_{}_{}.csv'.format(
                dataset_name, task_name,
                datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            )
        outfile.parents[0].mkdir(exist_ok=True)
        results_df.to_csv(outfile)


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

    print("Creating ExtractedFeatures...")
    for stim_object, result in progressbar(results):
        bulk_ees = []
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
                ExtractedEvent(stimulus_id=stim_object.id,
                               ef_id=ext_feats[feat_hash].id,
                               **ee_props))
        db.session.bulk_save_objects(bulk_ees)
        db.session.commit()

    return ext_feats


def create_predictors(features, dataset_name, task_name, run_ids=None,
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
    task = Task.query.filter_by(dataset_id=dataset.id)
    if task_name is not None:
        task.filter_by(name=task_name)

    task = task.one()

    # Create/Get Predictors
    all_preds = []
    for ef in features:
        # Calculate num of runs this feature is present in
        unique_runs = RunStimulus.query.filter(
            RunStimulus.stimulus_id.in_(
                set([ee.stimulus_id for ee in ef.extracted_events]))).\
                distinct('run_id')

        if unique_runs.count() / len(task.runs) > percentage_include:
            all_preds.append(get_or_create(
                Predictor, name=ef.feature_name, description=ef.description,
                dataset_id=dataset.id,
                source='extracted', ef_id=ef.id)[0])

    # Create PredictorRuns
    for ix, predictor in enumerate(progressbar(all_preds)):
        ef = features[ix]
        all_rs = []
        # For all instances for stimuli in this task's runs
        for ee in ef.extracted_events:
            query = RunStimulus.query.filter_by(stimulus_id=ee.stimulus_id)
            if run_ids is not None:
                query = query.filter(RunStimulus.run_id.in_(run_ids))
            all_rs += [(predictor.id, rs.run_id) for rs in query]

        all_rs = [PredictorRun(predictor_id=pred_id, run_id=run_id)
                  for pred_id, run_id in set(all_rs)]
        db.session.bulk_save_objects(all_rs)
        db.session.commit()

    return [p.id for p in all_preds]


def extract_features(graphs, dataset_name=None, task_name=None,
                     **serializer_kwargs):
    """ Extract features using pliers for a dataset/task
        Args:
            dataset_name - dataset name
            task_name - task name
            graphs - List of Graphs to apply to stimuli
            serializer_kwargs - Arguments to pass to FeatureSerializer
        Output:
            list of db ids of extracted features
    """
    if dataset_name is None:
        return [extract_features(
            graphs, dataset.name, None, **serializer_kwargs)
                for dataset in Dataset.query.filter_by(active=True)]

    elif task_name is None:
        dataset = Dataset.query.filter_by(name=dataset_name).one()
        return [extract_features(
            graphs, dataset.name, task.name, **serializer_kwargs)
                 for task in dataset.tasks]

    else:
        stims = _load_stim_models(dataset_name, task_name)

        results = _extract(graphs, stims)

        _to_csv(results, dataset_name, task_name)

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
    for stim_model in progressbar(stim_models):
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
        for sm, s in progressbar(stims):
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
