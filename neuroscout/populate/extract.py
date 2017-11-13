""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from os.path import realpath, join
import json
import re
import pandas as pd
import numpy as np

from pliers.stimuli import load_stims
from pliers.graph import Graph

from datalad import api as da
from datalad.auto import AutomagicIO

from flask import current_app

from bids.events import BIDSEventCollection

import populate
from .utils import hash_file, hash_str

from models import (Dataset,
    Run, Stimulus, RunStimulus, ExtractedFeature, ExtractedEvent)

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
        for feature_name in ext_res.features:
            # Load names
            extractor_name = ext_res.extractor.name

            ## Look up feature in schema, set to None if not found
            feature_schema = self.schema.get(
                extractor_name, {}).get(feature_name, {})

            unique = {}
            tr_attrs = [getattr(ext_res.extractor, a) \
                        for a in ext_res.extractor._log_attributes]
            unique['extractor_parameters'] = str(dict(
                zip(ext_res.extractor._log_attributes, tr_attrs)))

            properties = {}
            properties['extractor_name'] = extractor_name
            properties['feature_name'] = feature_schema.get(
                'rename', feature_name)
            properties['extractor_version'] = ext_res.extractor.VERSION
            properties['description'] = feature_schema.get('description')
            properties['active'] = feature_schema.get('active', True)
            results.append(properties)

        return results

def extract_features(db_session, dataset_name, task_name, graph_spec,
                     automagic=False, verbose=True, **filters):
    """ Extract features using pliers for a dataset/task
        Args:
            db_session - database session object
            dataset_name - dataset name
            task_name - task name
            graph_spec - pliers graph json spec location, or dictionary
            verbose - verbose output
            filters - additional identifiers for runs
            automagic - enable automagic and unlock stimuli with datalad
        Output:
            list of db ids of extracted features
    """
    dataset = Dataset.query.filter_by(name=dataset_name).one()
    dataset_id = dataset.id
    local_path = dataset.local_path

    if automagic:
        automagic = AutomagicIO()
        automagic.activate()

    # Load event files
    collection = BIDSEventCollection(local_path)
    collection.read(task=task_name, **filters)

    # Filter to only get stim files
    stim_pattern = 'stim_file/(.*)'
    stim_paths = [join(local_path, 'stimuli',
                          re.findall(stim_pattern, col)[0])
     for col in collection.columns
     if re.match(stim_pattern, col)]

    # Monkey-patched auto doesn't work, so get and unlock manually
    if automagic:
        da.get(stim_paths)
        da.unlock(stim_paths)

    # Get absolute path and load
    stims = load_stims([realpath(s) for s in stim_paths])

    # Construct and run the graph
    if isinstance(graph_spec, str):
        graph = Graph(spec=graph_spec)
    else:
        graph = Graph(nodes=graph_spec)

    results = graph.run(stims, merge=False)

    serializer = FeatureSerializer()
    extracted_features = {}
    for res in results:
        if np.array(res.data).size > 0:
            serialized = serializer.load(res)
            for i, feature in enumerate(res.features):
                """" Add new ExtractedFeature """
                # Hash extractor name + feature name
                ef_hash = hash_str(
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

                # Set onset for event
                if pd.isnull(res.onsets):
                    onset = None
                elif isinstance(res.onsets, float):
                    onset = res.onsets
                else:
                    onset = res.onsets[0]

                # Get or create ExtractedEvent
                ee_model = ExtractedEvent(onset=onset, stimulus_id=stimulus.id,
                                          history=res.history.string,
                                          ef_id=ef_model.id,
                                          value=res.data[0][i])

                # Add duration
                if pd.isnull(res.durations):
                    ee_model.duration = None
                elif isinstance(res.durations, float):
                    ee_model.duration = res.durations
                else:
                    ee_model.duration = res.durations[0]

                db_session.add(ee_model)
                db_session.commit()

    """" Create Predictors from Extracted Features """
    # For all instances for stimuli in this task's runs
    task_runstimuli = RunStimulus.query.join(
        Run).filter(
            Run.dataset_id == dataset_id and Run.task.name==task_name).all()

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
                    if ee.onset:
                        onsets.append(ee.onset + rs.onset)
                    else:
                        onsets.append(rs.onset)

                    durations.append(ee.duration)
                    if ee.value:
                        values.append(ee.value)

                # If only a single value was extracted, and there is no duration
                # Set to stimulus duration
                if (len(durations) == 1) and (durations[0] is None):
                    durations[0] = rs.duration

                predictor_name = '{}.{}'.format(ef.extractor_name, ef.feature_name)

                populate.add_predictor(db_session, predictor_name, dataset_id,
                                       rs.run_id, onsets, durations, values,
                                       ef_id=ef.id)

    return list(extracted_features.values())
