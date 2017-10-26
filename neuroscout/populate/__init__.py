""" Database population methods """

from .extract import extract_features
from .ingest import (ingest_from_json, add_predictor,
                     add_group_predictors, add_task)
from .modify import delete_task


__all__ = [
    'add_group_predictors',
    'add_predictor',
    'add_task',
    'delete_task',
    'extract_features',
    'ingest_from_json'
]
