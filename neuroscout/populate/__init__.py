""" Database population methods """

from .extract import extract_features
from .ingest import add_group_predictors, add_task
from .modify import delete_task
from .json import ingest_from_json
from .convert import convert_stimuli

__all__ = [
    'add_group_predictors',
    'add_task',
    'convert_stimuli',
    'delete_task',
    'extract_features',
    'ingest_from_json'
]
