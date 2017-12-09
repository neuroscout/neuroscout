""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from flask import current_app
import json
import re
import pandas as pd
import numpy as np

from pliers.stimuli import load_stims
from pliers.transformers import get_transformer
from datalad import api as da

import populate
from models import (Dataset, Task,
    Run, Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent)
from .utils import hash_file, hash_data

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

    def _annotate_feature(pattern, schema, feat, ext_hash, features):
        """ Annotate a single pliers extracted result
        Args:
            pattern - regex pattern to match feature name
            schema - sub-schema that matches feature name
            feat - feature name from pliers
            ext_hash - hash of the extractor
            features - list of all features
        """
        features.remove(feat)
        name = re.sub(pattern, schema['replace'], feat) \
            if 'replace' in schema else feat
        description = re.sub(pattern, schema['description'], feat) \
            if 'description' in schema else None

        # Look up feature in schema, set to None if not found
        properties = {
            'feature_name': name,
            'sha1_hash': hash_data(str(ext_hash) + name),
            'description': description,
            'active': schema.get('active', True)
            }

        return properties

    def load(self, res):
        """" Load and annotate features in an extractor result object.
        Args:
            res - Pliers ExtractorResult object
        Returns a dictionary of annotated features
        """
        features = res.features.copy()
        ext_hash = res.extractor.__hash__()

        annotated = []
        # Add all features in schema, popping features that match
        for pattern, schema in self.schema.get(res.extractor.name, {}).items():
            matching = filter(re.compile(pattern).match, features)
            annotated += [self._annotate_feature(
                pattern, schema, feat, ext_hash, features) for feat in matching]

        # Add all remaining features
        if self.add_all is True:
            annotated += [self._annotate_feature(
                ".*", {}, feat, ext_hash, features) for feat in features]

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

        return annotated

def extract_features(db_session, dataset_name, task_name, extractors,
                     verbose=True, automagic=False):
    """ Extract features using pliers for a dataset/task
        Args:
            db_session - database session object
            dataset_name - dataset name
            task_name - task name
            extractors - dictionary of extractor names to parameters
            verbose - verbose output
            automagic - enable Datalad
        Output:
            list of db ids of extracted features
    """
    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id

    # Load all active stimuli for task
    stim_objects = Stimulus.query.filter_by(active=True).join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    stim_paths = [s.path for s in stim_objects if s.parent_id is None]
    if automagic:
        # Monkey-patched auto doesn't work, so get and unlock manually
        da.get(stim_paths)
        da.unlock(stim_paths)
    stim_paths += [s.path for s in stim_objects if s.parent_id is not None]
    stims = load_stims(stim_paths)

    results = []
    for name, parameters in extractors:
        # For every extractor, extract from matching stims
        ext = get_transformer(name, **parameters)
        valid_stims = [s for s in stims if ext._stim_matches_input_types(s)]
        results += ext.transform(valid_stims)

    serializer = FeatureSerializer()
    extracted_features = {}
    for res in results:
        if np.array(res.data).size > 0:
            # Annotate results
            serialized = serializer.load(res)
            for i, feature in enumerate(res.features):
                """" Add new ExtractedFeature """
                # Hash extractor name + feature name
                ef_hash = serialized[i]['sha1_hash']
                # If we haven't already added this feature
                if ef_hash not in extracted_features:
                    # Create/get feature
                    ef_model = ExtractedFeature(**serialized[i])
                    db_session.add(ef_model)
                    db_session.commit()
                    extracted_features[ef_hash] = ef_model

                """" Add ExtractedEvents """
                # Get associated stimulus record
                filename = res.stim.history.source_file \
                            if res.stim.history \
                            else res.stim.filename
                stim_hash = hash_file(filename)
                stimulus = db_session.query(
                    Stimulus).filter_by(sha1_hash=stim_hash).one()

                def grab_value(val):
                    if pd.isnull(val):
                        return None
                    elif isinstance(val, float):
                        return val
                    else:
                        return val[0]

                # Get or create ExtractedEvent
                ee_model = ExtractedEvent(onset=grab_value(res.onsets),
                                          duration=grab_value(res.durations),
                                          stimulus_id=stimulus.id,
                                          history=res.history.string,
                                          ef_id=ef_model.id,
                                          value=res.data[0][i])
                db_session.add(ee_model)
                db_session.commit()

    """" Create Predictors from Extracted Features """
    # Active stimuli from this task
    active_stims = db_session.query(Stimulus.id).filter_by(active=True). \
        join(RunStimulus).join(Run).join(Task).filter_by(name=task_name). \
        join(Dataset).filter_by(name=dataset_name)
    # For all instances for stimuli in this task's runs
    task_runstimuli = RunStimulus.query.filter(
        RunStimulus.stimulus_id.in_(active_stims))

    for rs in task_runstimuli:
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

                predictor_name = '{}.{}'.format(
                    ef.extractor_name, ef.feature_name)

                populate.add_predictor(db_session, predictor_name, dataset_id,
                                       rs.run_id, onsets, durations, values,
                                       ef_id=ef.id)

    return list(extracted_features.values())
