""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from flask import current_app
from database import db
import json
import re
import pandas as pd
from pathlib import Path
import datetime
import progressbar

from pliers.stimuli import load_stims
from pliers.transformers import get_transformer
from pliers.extractors import merge_results

import populate
from models import (Dataset, Task,
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
        self.features.remove(feat)

        name = re.sub(pattern, schema['replace'], feat) \
            if 'replace' in schema else feat
        description = re.sub(pattern, schema['description'], feat) \
            if 'description' in schema else None

        properties = [{
            'feature_name': name,
            'sha1_hash': hash_data(str(ext_hash) + name),
            'description': description,
            'active': schema.get('active', default_active),
            'value': v['value'],
            'object_id': v['object_id'],
            } for i, v in sub_df.iterrows()]

        return properties

    def load(self, res):
        """" Load and annotate features in an extractor result object.
        Args:
            res - Pliers ExtractorResult object
        Returns a dictionary of annotated features
        """
        res_df = res.to_df(format='long')
        self.features = res_df['feature'].tolist()
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
            matching = filter(re.compile(pattern).match, self.features)
            for feat in matching:
                annotated += self._annotate_feature(
                    pattern, schema, feat, ext_hash, res_df[res_df.feature == feat])

        # Add all remaining features
        if self.add_all is True:
            for feat in self.features.copy():
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
        for a in annotated:
            a.update(constants)

        ## Only return non-null values
        annotated = [a for a in annotated if a['value'] is not None]

        return annotated

def grab_value(val):
    if pd.isnull(val):
        return None
    elif isinstance(val, float):
        return val
    else:
        return val[0]

def extract_features(dataset_name, task_name, extractors):
    """ Extract features using pliers for a dataset/task
        Args:
            dataset_name - dataset name
            task_name - task name
            extractors - dictionary of extractor names to parameters
        Output:
            list of db ids of extracted features
    """
    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id

    # Load all active stimuli for task
    stim_objects = Stimulus.query.filter_by(active=True).join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    stim_paths = [s.path for s in stim_objects if s.parent_id is None]
    stim_paths += [s.path for s in stim_objects if s.parent_id is not None]
    stims = load_stims(stim_paths)

    results = []
    for name, parameters in extractors:
        # For every extractor, extract from matching stims
        ext = get_transformer(name, **parameters)
        valid_stims = [s for s in stims if ext._stim_matches_input_types(s)]
        results += ext.transform(valid_stims)

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

    with progressbar.ProgressBar(max_value=len(results)) as bar:
        serializer = FeatureSerializer()
        extracted_features = {}
        for i, res in enumerate(results):
            if res._data != [{}]:
                # Annotate results
                for feature in serializer.load(res):
                    """" Add new ExtractedFeature """
                    # Hash extractor name + feature name
                    ef_hash = feature['sha1_hash']
                    value = feature.pop('value')
                    object_id = feature.pop('object_id')
                    # If we haven't already added this feature
                    if ef_hash not in extracted_features:
                        # Create/get feature
                        ef_model = ExtractedFeature(**feature)
                        db.session.add(ef_model)
                        db.session.commit()
                        extracted_features[ef_hash] = ef_model

                    """" Add ExtractedEvents """
                    # Get associated stimulus record
                    stim_hash = hash_stim(res.stim)
                    stimulus = db.session.query(
                        Stimulus).filter_by(sha1_hash=stim_hash).one()

                    # Get or create ExtractedEvent
                    ee_model = ExtractedEvent(onset=grab_value(res.onset),
                                              duration=grab_value(res.duration),
                                              stimulus_id=stimulus.id,
                                              history=res.history.string,
                                              ef_id=ef_model.id,
                                              value=value,
                                              object_id=object_id)
                    db.session.add(ee_model)
                    db.session.commit()
            bar.update(i)

    current_app.logger.info("Creating predictors")
    """" Create Predictors from Extracted Features """
    # Active stimuli from this task
    active_stims = db.session.query(Stimulus.id).filter_by(active=True). \
        join(RunStimulus).join(Run).join(Task).filter_by(name=task_name). \
        join(Dataset).filter_by(name=dataset_name)
    # For all instances for stimuli in this task's runs
    task_runstimuli = RunStimulus.query.filter(
        RunStimulus.stimulus_id.in_(active_stims)).all()

    with progressbar.ProgressBar(max_value=len(task_runstimuli)) as bar:
        for i, rs in enumerate(task_runstimuli):
            # For every feature extracted
            for ef_hash, ef in extracted_features.items():
                if ef.active:
                    ### Abstract some of this logic out for derived features
                    # Get ExtractedEvents associated with stimulus
                    ees = ef.extracted_events.filter_by(
                        stimulus_id = rs.stimulus_id).all()

                    onsets = []
                    durations = []
                    values = []
                    for ee in ees:
                        onsets.append((ee.onset or 0 )+ rs.onset)
                        durations.append(ee.duration)
                        if ee.value:
                            values.append(ee.value)

                    # If only a single value was extracted, and there is no duration
                    # Set to stimulus duration
                    if (len(durations) == 1) and (durations[0] is None):
                        durations[0] = rs.duration

                    populate.add_predictor(
                        ef.feature_name, dataset_id, rs.run_id, onsets, durations,
                        values, source='extracted', ef_id=ef.id)
        bar.update(i)

    return list(extracted_features.values())
