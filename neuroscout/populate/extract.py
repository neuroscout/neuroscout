""" Feature extraction methods
Set of methods to extract features from stimuli in a dataset and generate
the associated predictors
"""
from os.path import realpath, join
import json
import re
import pandas as pd
import imageio

from datalad import api as da

from flask import current_app

from bids.events import BIDSEventCollection

import populate
import db_utils
from .utils import hash_file, hash_str

from models import (
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
        # Load names
        extractor_name = ext_res.extractor.name
        feature_name = ext_res.features[0]

        ## Look up feature in schema, set to None if not found
        feature_schema = self.schema.get(
            extractor_name, {}).get(feature_name, {})

        unique = {}
        tr_attrs = [getattr(ext_res, a) for a in ext_res.extractor._log_attributes]
        unique['extractor_parameters'] = str(dict(
            zip(ext_res.extractor._log_attributes, tr_attrs)))
        unique['extractor_name'] = extractor_name
        unique['feature_name'] = feature_schema.get('rename', feature_name)
        unique['extractor_version'] = ext_res.extractor.VERSION

        extra = {}
        extra['description'] = feature_schema.get('description')
        extra['active'] = feature_schema.get('active', True)

        return unique, extra

def extract_features(db_session, local_path, name, task, graph_spec,
                     automagic=False, verbose=True, **filters):
    """ Extract features using pliers for a dataset/task
        Args:
            db_session - db db_session
            local_path - bids dataset directory
            task - task name
            graph_spec - pliers graph json spec location
            verbose - verbose output
            filters - additional identifiers for runs
            automagic - enable automagic and unlock stimuli with datalad
        Output:
            list of db ids of extracted features
    """
    try:
        from pliers.stimuli import load_stims
        from pliers.graph import Graph
    except imageio.core.fetching.NeedDownloadError:
        imageio.plugins.ffmpeg.download()
        from pliers.stimuli import load_stims
        from pliers.graph import Graph

    # ### CHANGE THIS TO LOOK UP ONLY. FAIL IF DS NOT FOUND
    dataset_id = populate.add_task(db_session, task, local_path=local_path,
                             name=name, **filters)


    # Load event files
    collection = BIDSEventCollection(local_path)
    collection.read(task=task, **filters)

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
    graph = Graph(spec=graph_spec)
    results = graph.run(stims, merge=False)

    serializer = FeatureSerializer()

    extracted_features = {}
    for res in results:
        """" Add new ExtractedFeature """
        # Hash extractor name + feature name
        ef_hash = hash_str(str(res.extractor.__hash__()) + res.features[0])

        # If we haven't already added this feature from this extractor + params
        if ef_hash not in extracted_features:
            unique, extra = serializer.load(res)
            # Create/get feature
            ef_model, _ = db_utils.get_or_create(db_session,
                                                 ExtractedFeature,
                                                 commit=False, **unique)

            # Add non identifying information and commit
            ef_model.sha1_hash = ef_hash
            for key, value in extra.items():
                setattr(ef_model, key, value)
            db_session.commit()
            extracted_features[ef_hash] = (ef_model.id, ef_model.active)

        """" Add ExtractedEvents """
        # Get associated stimulus record
        filename = res.stim.history.source_file \
                    if res.stim.history \
                    else res.stim.filename
        stim_hash = hash_file(filename)
        stimulus = db_session.query(Stimulus).filter_by(sha1_hash=stim_hash).one()

        # Set onset for event
        if pd.isnull(res.onsets):
            onset = None
        elif isinstance(res.onsets, float):
            onset = res.onsets
        else:
            onset = res.onsets[0]

        # Get or create ExtractedEvent
        ee_model, ee_new = db_utils.get_or_create(db_session,
                                               ExtractedEvent,
                                               commit=False,
                                               onset=onset,
                                               stimulus_id=stimulus.id,
                                               ef_id=extracted_features[ef_hash][0])

        # Add data to it (whether or not its new, as we may want to update)
        ee_model.value = res.data[0][0]
        if pd.isnull(res.durations):
            ee_model.duration = None
        elif isinstance(res.durations, float):
            ee_model.duration = res.durations
        else:
            ee_model.duration = res.durations[0]

        ee_model.history = res.history.string

        db_session.commit()

    """" Create Predictors from Extracted Features """
    # For all instances for stimuli in this task's runs
    task_runstimuli = RunStimulus.query.join(
        Run).filter(Run.dataset_id == dataset_id and Run.task.name==task).all()
    for rs in task_runstimuli:
        # For every feature extracted
        for ef, (ef_id, active) in extracted_features.items():
            if active:
                ### Abstract some of this logic out for when we later create derived features
                ef = ExtractedFeature.query.filter_by(id = ef_id).one()
                # Get ExtractedEvents associated with stimulus
                ees = ef.extracted_events.filter_by(
                    stimulus_id = rs.stimulus_id).all()

                onsets = [ee.onset + rs.onset if ee.onset else rs.onset
                          for ee in ees]
                durations = [ee.duration for ee in ees]

                # If only a single value was extracted, and there is no duration
                # Set to stimulus duration
                if (len(durations) == 1) and (durations[0] is None):
                    durations[0] = rs.duration

                values = [ee.value for ee in ees if ee.value]

                predictor_name = '{}.{}'.format(ef.extractor_name, ef.feature_name)

                populate.add_predictor(db_session, predictor_name, dataset_id, rs.run_id,
                              onsets, durations, values, ef_id = ef_id,
                              description=ef.description)

    return list(extracted_features.values())
