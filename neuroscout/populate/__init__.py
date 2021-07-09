""" Database population methods """

from .extract import extract_features
from .ingest import add_group_predictors, add_task, add_dataset
from .modify import delete_task
from .setup import ingest_from_json, setup_dataset
from .convert import convert_stimuli

__all__ = [
    'add_group_predictors',
    'add_task',
    'add_dataset',
    'convert_stimuli',
    'delete_task',
    'extract_features',
    'ingest_from_json',
    'setup_dataset'
]
