""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from flask import current_app
import json
import pandas as pd
import numpy as np

from pliers.stimuli import load_stims
import pliers.extractors
from datalad import api as da

import populate
from models import (Dataset, Task,
    Run, Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent)
from .utils import hash_file, hash_data

class FeatureSerializer(object):
    """ Serialized Pliers results from a schema containing additional
        meta-data """
    def __init__(self, schema=None):
        if schema is None:
            schema = current_app.config['FEATURE_SCHEMA']
        self.schema = json.load(open(schema, 'r'))

    def load(self, ext_res):
        """" Load a single pliers feature result to dictionaries.

        Output is split into uniquely identifying attributes, and additional
        attributes.
        """
        results = []
        extractor_name = ext_res.extractor.name
        for feature_name in ext_res.features:
            # Look up feature in schema, set to None if not found
            feature_schema = self.schema.get(
                extractor_name, {}).get(feature_name, {})

            properties = {}
            properties['extractor_name'] = extractor_name
            tr_attrs = [getattr(ext_res.extractor, a) \
                        for a in ext_res.extractor._log_attributes]
            properties['extractor_parameters'] = str(dict(
                zip(ext_res.extractor._log_attributes, tr_attrs)))
            properties['feature_name'] = feature_schema.get(
                'rename', feature_name)
            properties['extractor_version'] = ext_res.extractor.VERSION
            properties['description'] = feature_schema.get('description')
            properties['active'] = feature_schema.get('active', True)
            results.append(properties)

        return results

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
    for extractor_name, parameters in extractors.items():
        # For every extractor, extract from matching stims
        ext = getattr(pliers.extractors, extractor_name)(**parameters)
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
                ef_hash = hash_data(
                    str(res.extractor.__hash__()) + res.features[i])

                # If we haven't already added this feature
                if ef_hash not in extracted_features:
                    # Create/get feature
                    ef_model = ExtractedFeature(sha1_hash=ef_hash,
                                                **serialized[i])
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
