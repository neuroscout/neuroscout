from flask import current_app
import numpy as np
import json
import re
import pandas as pd
from pliers.utils import resample
from .utils import hash_data
from ..utils.core import listify


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
    def __init__(self, add_all=True, include=None, exclude=None, TR=None):
        """ Initialize serializer for ingested features.
        Args:
            add_all - Add all variables including those not in the schema
            include - List of variables to include
            exclude - List of variables to exclude
            TR - TR in seconds
        """
        self.include = include
        self.exclude = exclude
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
        if self.exclude is not None and variable.name in self.exclude:
            return None

        annotated = {}
        annotated['original_name'] = variable.name
        annotated['source'] = variable.source

        for pattern, attr in self.schema.items():
            if re.compile(pattern).match(variable.name):
                annotated['name'] = re.sub(
                    pattern, attr.pop('name'), variable.name) \
                    if 'name' in attr else variable.name
                annotated['description'] = re.sub(
                    pattern, attr.pop('description'), variable.name) \
                    if 'description' in attr else None
                annotated.update(**attr)  # Add any additional attributes
                break
        else:
            annotated['name'] = variable.name
            if self.add_all is False:
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

            onsets = np.arange(
                0, len(variable.values) * self.TR, self.TR).tolist()
            durations = [(self.TR)] * len(variable.values)
            values = variable.values[variable.name].values.tolist()

        events = []
        for i, onset in enumerate(onsets):
            try:
                events.append(
                    {
                        'onset': onset,
                        'duration': durations[i],
                        'value': values[i]
                    }
                )
            except IndexError:
                if len(onsets) - len(values) == 1:
                    pass
                else:
                    raise IndexError

        return annotated, events


stim_map = {
    'ImageStim': 'image',
    'VideoStim': 'video',
    'TextStim': 'text',
    'ComplexTextStim': 'text',
    'AudioStim': 'audio'
}


class FeatureSerializer(Serializer):
    def __init__(self, add_all=True, object_id='all', splat=False,
                 round_n=None, resample_frequency=None):
        """
        Args:
            add_all - Add all features including those with no match in
                      feature_schema
            object_id - How to select among object_id repetitions
                        One of: max, all
            splat - If value is a list, automatically create n features,
            round_n - Round float values to nth precision
            resample_frequency - Frequency to resample events to in Hz.
                If None, will defer to value for that extractor if
                predictor_schema.json. If not specified, will default to 3hz.
                If False, will skip resampling, regardless of value in schema.
        """
        self.object_id = object_id
        self.splat = splat
        self.round_n = round_n
        self.resample_frequency = resample_frequency
        super().__init__(current_app.config['FEATURE_SCHEMA'], add_all)

    def _annotate_feature(self, pattern, schema, feat, extractor, sub_df,
                          default_active=True, resample_frequency=None):
        """ Annotate a single pliers extracted result
        Args:
            pattern - regex pattern to match feature name
            schema - sub-schema that matches feature name
            feat - feature name from pliers
            extractor - pliers extractor object
            sub_df - df with ef values
            default_active - set to active by default?
        """
        # If name is in schema, substitute regex patterns from schema pattern
        # and fill in format strings from extractor_dict
        feat = feat.replace(',', '')  # Remove commas
        if 'name' in schema:
            name = re.sub(pattern, schema['name'], feat)
            name = name.format(**extractor.__dict__)
        else:
            name = feat

        if 'description' in schema:
            description = re.sub(pattern, schema['description'], feat)
            description = description.format(**extractor.__dict__)
        else:
            description = None

        if not resample_frequency:
            resample_frequency = None

        annotated = []
        for _, row in sub_df[sub_df.value.notnull()].iterrows():
            if isinstance(row['value'], list) and not self.splat:
                raise ValueError("Value is an array and splatting is not True")
            val = listify(row['value'])

            for ix, v in enumerate(val):
                feature_name = f"{name}_{ix+1}" if len(val) > 1 else name
                if self.round_n is not None and isinstance(v, float):
                    v = round(v, self.round_n)

                ee = {
                    'value': v,
                    'onset': row['onset']
                    if not pd.isnull(row['onset']) else None,
                    'duration': row['duration']
                    if not pd.isnull(row['duration']) else None,
                    'object_id': row.get('object_id', None)
                    }
                ef = {
                    'sha1_hash': hash_data(
                        str(extractor.__hash__()) + feature_name),
                    'feature_name': feature_name,
                    'original_name': feat,
                    'description': description,
                    'active': schema.get('active', default_active),
                    'resample_frequency': resample_frequency
                    }

                annotated.append((ee, ef))
        return annotated

    def load(self, res):
        """" Load and annotate features in an extractor result object.
        Args:
            res - Pliers ExtractorResult object

        Returns a dictionary of annotated features
        """
        res_df = res.to_df(format='long')
        if self.object_id == 'max':
            res_df = res_df[res_df.object_id == res_df.object_id.max()]
        features = res_df['feature'].unique().tolist()

        # Find matching extractor schema + attribute combination
        # Entries with no attributes will match any
        ext_schema = {}
        for candidate in self.schema.get(res.extractor.name, []):
            for name, value in candidate.get("attributes", {}).items():
                if getattr(res.extractor, name) != value:
                    break
            else:
                ext_schema = candidate

        # Determine resample frequency. False value will skip
        resample_frequency = self.resample_frequency
        if resample_frequency is None:
            resample_frequency = ext_schema.get('resample_frequency', False)

        # Resample events if
        if resample_frequency:
            res_df = resample(res_df, resample_frequency)

        annotated = []
        # Add all features in schema, popping features that match
        for pattern, schema in ext_schema.get('features', {}).items():
            matching = list(filter(re.compile(pattern).match, features))
            features = set(features) - set(matching)
            for feat in matching:
                annotated += self._annotate_feature(
                    pattern, schema, feat, res.extractor,
                    res_df[res_df.feature == feat],
                    resample_frequency=resample_frequency)

        # Add all remaining features
        if self.add_all is True:
            for feat in features:
                annotated += self._annotate_feature(
                    ".*", {}, feat, res.extractor,
                    res_df[res_df.feature == feat], default_active=False,
                    resample_frequency=resample_frequency)

        # Add extractor constants
        tr_attrs = [getattr(res.extractor, a)
                    for a in res.extractor._log_attributes]
        constants = {
            "extractor_name": res.extractor.name,
            "extractor_parameters": str(dict(
                zip(res.extractor._log_attributes, tr_attrs))),
            "extractor_version": res.extractor.VERSION,
            "modality": stim_map.get(res.extractor._input_type.__name__, '')
        }

        for ee, ef in annotated:
            ef.update(constants)

        return annotated
