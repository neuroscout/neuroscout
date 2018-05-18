""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from flask import current_app
import json
import re
import pandas as pd
from pathlib import Path
import datetime
from progressbar import progressbar

from pliers.stimuli import load_stims, ComplexTextStim, TextStim
from pliers.transformers import get_transformer
from pliers.extractors import merge_results

from ..app import db
from ..utils import get_or_create
from ..models import (Dataset, Task, Predictor, PredictorEvent, PredictorRun,
    Run, Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent)
from .utils import hash_data, hash_stim

class FeatureSerializer(object):
    def __init__(self, schema=None, add_all=True):
        """ Serialize and annotate Pliers results using a schema.
        Args:
            schema - json schema file
            add_all - serialize features that are not in the schema
        """
        if schema is None:
            schema = current_app.config['FEATURE_SCHEMA']
        self.schema = json.load(open(schema, 'r'))
        self.add_all=True

    def _annotate_feature(self, pattern, schema, feat, ext_hash, sub_df,
                          default_active=True):
        """ Annotate a single pliers extracted result
        Args:
            pattern - regex pattern to match feature name
            schema - sub-schema that matches feature name
            feat - feature name from pliers
            ext_hash - hash of the extractor
            features - list of all features
            default_active - set to active by default?
        """
        name = re.sub(pattern, schema['replace'], feat) \
            if 'replace' in schema else feat
        description = re.sub(pattern, schema['description'], feat) \
            if 'description' in schema else None

        annotated = []
        for i, v in sub_df[sub_df.value.notnull()].iterrows():
            annotated.append(
                (
                    {
                        'value': v['value'],
                        'onset': v['onset'] if not pd.isnull(v['onset']) else None,
                        'duration': v['duration'] if not pd.isnull(v['duration']) else None,
                        'object_id': v['object_id']
                        },
                    {
                        'sha1_hash': hash_data(str(ext_hash) + name),
                        'feature_name': name,
                        'description': description,
                        'active': schema.get('active', default_active),
                        }
                    )
                )

        return annotated

    def load(self, res):
        """" Load and annotate features in an extractor result object.
        Args:
            res - Pliers ExtractorResult object
        Returns a dictionary of annotated features
        """
        res_df = res.to_df(format='long')
        features = res_df['feature'].unique().tolist()
        ext_hash = res.extractor.__hash__()

        # Find matching extractor schema + attribute combination
        # Entries with no attributes will match any
        ext_schema = {}
        for candidate in self.schema.get(res.extractor.name, []):
            for name, value in candidate.get("attributes", {}).items():
                if getattr(res.extractor, name) != value:
                    break
            else:
                ext_schema = candidate

        annotated = []
        # Add all features in schema, popping features that match
        for pattern, schema in ext_schema.get('features', {}).items():
            matching = list(filter(re.compile(pattern).match, features))
            features = set(features) - set(matching)
            for feat in matching:
                annotated += self._annotate_feature(
                    pattern, schema, feat, ext_hash, res_df[res_df.feature == feat])

        # Add all remaining features
        if self.add_all is True:
            for feat in features:
                annotated += self._annotate_feature(
                    ".*", {}, feat, ext_hash,
                    res_df[res_df.feature == feat], default_active=False)

        # Add extractor constants
        tr_attrs = [getattr(res.extractor, a) \
                    for a in res.extractor._log_attributes]
        constants = {
            "extractor_name": res.extractor.name,
            "extractor_parameters": str(dict(
                zip(res.extractor._log_attributes, tr_attrs))),
            "extractor_version": res.extractor.VERSION
        }
        for ee, ef in annotated:
            ef.update(constants)

        return annotated


def load_stim_objects(dataset_name, task_name):
    """ Given a dataset and task, load all available stimuli as Pliers
    stimuli """
    stim_objects = Stimulus.query.filter_by(active=True).join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    # Order
    all_stims = [s for s in stim_objects if s.parent_id is None]
    all_stims += [s for s in stim_objects if s.parent_id is not None]

    stims = []
    for stim_object in all_stims:
        if stim_object.path is None:
            complex = ComplexTextStim(text=stim_object.content)
            stims.append(complex)
            stims.append(TextStim(text=complex.data)) # Append both ways
        else:
            stims.append(load_stims(stim_object.path))

    return stims


def extract_features(dataset_name, task_name, extractors):
    """ Extract features using pliers for a dataset/task
        Args:
            dataset_name - dataset name
            task_name - task name
            extractors - dictionary of extractor names to parameters
        Output:
            list of db ids of extracted features
    """
    # Load all active stimuli for task
    stims = load_stim_objects(dataset_name, task_name)

    results = []
    for name, parameters in extractors:
        # For every extractor, extract from matching stims
        ext = get_transformer(name, **parameters)
        results += ext.transform(
            [s for s in stims if ext._stim_matches_input_types(s)]
            )

    # Save results to file
    if results != [] and 'EXTRACTION_DIR' in current_app.config:
        results_df = merge_results(results)
        results_path = Path(current_app.config['EXTRACTION_DIR']).absolute() / \
            '{}_{}_{}.csv'.format(
                dataset_name, task_name,
                datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                )
        results_path.parents[0].mkdir(exist_ok=True)
        results_df.to_csv(results_path.as_posix())

    serializer = FeatureSerializer()
    extracted_features = {}
    for res in progressbar(results):
        bulk_ees = []
        for ee_props, ef_props in serializer.load(res):
            """" Add new ExtractedFeature """
            # Hash extractor name + feature name
            feat_hash = ef_props['sha1_hash']

            # If we haven't already added this feature
            if feat_hash not in extracted_features:
                # Create/get feature
                ef_model = ExtractedFeature(**ef_props)
                db.session.add(ef_model)
                db.session.commit()
                extracted_features[feat_hash] = ef_model
            else:
                ef_model = extracted_features[feat_hash]

            """" Add ExtractedEvents """
            # Get associated stimulus record
            stim_hash = hash_stim(res.stim)
            stimulus = db.session.query(
                Stimulus).filter_by(sha1_hash=stim_hash).one_or_none()

            # If hash fails, use filename
            if stimulus is None:
                stimulus = db.session.query(
                    Stimulus).filter_by(path=res.stim.filename).one()

            # Get or create ExtractedEvent
            bulk_ees.append(
                ExtractedEvent(stimulus_id=stimulus.id,
                               history=res.history.string,
                               ef_id=ef_model.id,
                               **ee_props))
        db.session.bulk_save_objects(bulk_ees)
        db.session.commit()

    create_predictors(
        [ef for ef in extracted_features.values() if ef.active],
        dataset_name
        )

    return list(extracted_features.values())


def create_predictors(features, dataset_name):
    """" Create Predictors from Extracted Features """
    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id

    current_app.logger.info("Creating predictors")
    all_preds = []
    for ef in features:
        all_preds.append(get_or_create(
            Predictor, name=ef.feature_name, dataset_id=dataset_id,
            source='extracted', ef_id=ef.id)[0])


    current_app.logger.info("Creating predictor events")
    for ix, predictor in enumerate(progressbar(all_preds)):
        ef = features[ix]
        all_pes = []
        all_rs = []
        # For all instances for stimuli in this task's runs
        for ee in ef.extracted_events:
            # if ee.value:
            for rs in RunStimulus.query.filter_by(stimulus_id=ee.stimulus_id):
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
