from flask import current_app
import numpy as np
import json
import re
import pandas as pd
from .utils import hash_data

class Serializer(object):
    def __init__(self, schema, add_all):
        """ Serialize and annotate results using a schema.
        Args:
            schema - json schema file
            add_all - serialize features that are not in the schema
        """
        self.schema = json.load(open(schema, 'r'))
        self.add_all = add_all

class PredictorSerializer(Serializer):
    def __init__(self, add_all=True, include=None, TR=None):
        """ Initalize serializer for ingested features.
        Args:
            add_all - Add all variables including those not in the schema
            include - List of variables to include
            TR - TR in seconds
        """
        self.include = include
        self.TR = TR
        super().__init__(current_app.config['PREDICTOR_SCHEMA'], add_all)

    def load(self, variable):
        """" Load and annotate a BIDSVariable
        Args:
            res - BIDSVariableCollection object
        Returns a dictionary of annotated features
        """
        if self.include is not None and variable.name not in self.include:
            return None

        annotated = {}
        annotated['original_name'] = variable.name
        annotated['source'] = variable.source

        for pattern, attr in self.schema.items():
            if re.compile(pattern).match(variable.name):
                annotated['name'] = re.sub(pattern, attr['name'], variable.name) \
                    if 'name' in attr else variable.name
                annotated['description'] = re.sub(pattern, attr['description'], variable.name) \
                    if 'description' in attr else None
                break
        else:
            annotated['name'] = variable.name
            if self.add_all == False:
                return None

        # If SparseVariable
        if hasattr(variable, 'onset'):
            onsets = variable.onset.tolist()
            durations = variable.duration.tolist()
            values = variable.values.values.tolist()

        # If Dense, resample, and sparsify
        else:
            TR = variable.sampling_rate / 2 if self.TR is None else self.TR
            variable = variable.resample(1 / TR)

            onsets = np.arange(0, len(variable.values) * self.TR, self.TR).tolist()
            durations = [(self.TR)] * len(variable.values)
            values = variable.values[variable.name].values.tolist()

        events = []
        for i, onset in enumerate(onsets):
            events.append(
                {
                    'onset': onset,
                    'duration': durations[i],
                    'value': values[i]
                 }
            )

        return annotated, events

stim_map = {
    'ImageStim': 'image',
    'VideoStim': 'video',
    'TextStim': 'text',
    'AudioStim': 'audio'
}

class FeatureSerializer(Serializer):
    def __init__(self, add_all=True):
        super().__init__(current_app.config['FEATURE_SCHEMA'], add_all)

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
        name = re.sub(pattern, schema['name'], feat) \
            if 'name' in schema else feat
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
                        'original_name': feat,
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
            "extractor_version": res.extractor.VERSION,
            "modality": stim_map[res.extractor._input_type.__name__]
        }


        for ee, ef in annotated:
            ef.update(constants)

        return annotated
