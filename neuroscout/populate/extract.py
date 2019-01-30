""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from flask import current_app
from core import cache
from database import db
import socket

from pathlib import Path
import datetime
from progressbar import progressbar
from utils import get_or_create

from pliers.stimuli import load_stims, ComplexTextStim, TextStim
from pliers.transformers import get_transformer
from pliers.extractors import merge_results

from models import (Dataset, Task, Predictor, PredictorEvent, PredictorRun,
                    Run, Stimulus, RunStimulus,
                    ExtractedFeature, ExtractedEvent)
from .annotate import FeatureSerializer

socket.setdefaulttimeout(10000)


def _load_stim_models(dataset_name, task_name):
    """ Given a dataset and task, load all available stimuli as Pliers
    stimuli, and pair them with original database stim object. """
    stim_models = Stimulus.query.filter_by(active=True).join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    stims = []
    for stim_model in stim_models:
        if stim_model.path is None:
            # Load both ways for Text stimuli
            stims.append(
                (stim_model, ComplexTextStim(text=stim_model.content)))
            stims.append(
                (stim_model, TextStim(text=stims[-1][1].data)))
        else:
            stims.append(
                (stim_model, load_stims(stim_model.path)))

    return stims


def _extract(extractors, stims):
    results = []
    for name, parameters in extractors:
        # For every extractor, extract from matching stims
        current_app.logger.info("Extractor: {}".format(name))
        ext = get_transformer(name, **parameters)
        for stim_model, stim in stims:
            if ext._stim_matches_input_types(stim):
                # Hacky workaround. Look for compatible AVI
                if 'GoogleVideoAPIShotDetectionExtractor' in str(ext.__class__):
                    stim.filename = Path(
                        stim.filename).with_suffix('.avi').as_posix()
                results.append((stim_model, ext.transform(stim)))
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


def extract_features(dataset_name, task_name, extractors):
    """ Extract features using pliers for a dataset/task
        Args:
            dataset_name - dataset name
            task_name - task name
            extractors - dictionary of extractor names to parameters
        Output:
            list of db ids of extracted features
    """
    cache.clear()
    stims = _load_stim_models(dataset_name, task_name)

    results = _extract(extractors, stims)

    _to_csv(results, dataset_name, task_name)

    ext_feats = {}
    for stim_object, result in progressbar(results):
        bulk_ees = []
        for ee_props, ef_props in FeatureSerializer().load(result):
            # Hash extractor name + feature name
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
                               history=result.history.string,
                               ef_id=ext_feats[feat_hash].id,
                               **ee_props))
        db.session.bulk_save_objects(bulk_ees)
        db.session.commit()

    return create_predictors([ef for ef in ext_feats.values() if ef.active],
                             dataset_name)


def create_predictors(features, dataset_name, run_ids=None):
    """ Create Predictors from Extracted Features.
        Args:
            features (object) - ExtractedFeature objects
            dataset_name (str) - Dataset name
            run_ids (list of ints) - Optional list of run_ids for which to
                                     create PredictorEvents for.
    """
    current_app.logger.info("Creating predictors")

    # Create/Get Predictors
    all_preds = []
    for ef in features:
        all_preds.append(get_or_create(
            Predictor, name=ef.feature_name, description=ef.description,
            dataset_id=Dataset.query.filter_by(name=dataset_name).one().id,
            source='extracted', ef_id=ef.id)[0])

    # Create PredictorEvents and PredictorRuns
    for ix, predictor in enumerate(progressbar(all_preds)):
        ef = features[ix]
        all_pes = []
        all_rs = []
        # For all instances for stimuli in this task's runs
        for ee in ef.extracted_events:
            # if ee.value:
            query = RunStimulus.query.filter_by(stimulus_id=ee.stimulus_id)
            if run_ids is not None:
                query = query.filter(RunStimulus.run_id.in_(run_ids))
            for rs in query:
                    all_rs.append((predictor.id, rs.run_id))
                    duration = ee.duration
                    if duration is None:
                        duration = rs.duration
                    all_pes.append(
                        PredictorEvent(
                            onset=(ee.onset or 0) + rs.onset,
                            value=ee.value,
                            object_id=ee.object_id,
                            duration=duration,
                            predictor_id=predictor.id,
                            run_id=rs.run_id,
                            stimulus_id=ee.stimulus_id
                        )
                    )

        all_rs = [PredictorRun(predictor_id=pred_id, run_id=run_id)
                  for pred_id, run_id in set(all_rs)]
        db.session.bulk_save_objects(all_pes + all_rs)
        db.session.commit()

    return [p.id for p in all_preds]
