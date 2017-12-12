import json
from flask import current_app
from pathlib import Path
from .ingest import add_task
from .extract import extract_features
from .convert import convert_stimuli
from models import Dataset
from copy import deepcopy
import os
from pliers.utils.updater import check_updates

def get_delta_config(db_session, config_dict):
    """ Returns element of config file that must be re-extracted """
    # Get set of extractors that are used
    config_dict = deepcopy(config_dict)
    transformers = []
    for _, dataset in config_dict.items():
        for _, task in dataset['tasks'].items():
         transformers += task.get('extractors', [])
         transformers += task.get('converters', [])

    # Check for updates
    datastore = current_app.config['FEATURE_DATASTORE']
    os.makedirs(os.path.dirname(datastore), exist_ok=True)

    updated = check_updates(transformers, datastore=datastore)

    filt_config = {}
    for dname, dataset in config_dict.items():
        new_tasks = {}
        for tname, task in dataset.pop('tasks').items():
            filt_ext = [e for e in task.get('extractors', []) \
                        if tuple(e) in updated['transformers']]
            filt_conv = [c for c in task.get('converters', []) \
                        if tuple(c) in updated['transformers']]

            if filt_ext or filt_conv:
                task['extractors'] = filt_ext
                task['converters'] = filt_conv
                new_tasks[tname] = task

        if new_tasks:
            dataset['tasks'] = new_tasks
            filt_config[dname] = dataset

    return filt_config

def ingest_from_json(db_session, config_file, automagic=False, update=False):
    all_transformers = json.load(
        open(current_app.config['ALL_TRANSFORMERS'], 'r'))
    dataset_config = json.load(open(config_file, 'r'))
    updated_config = get_delta_config(db_session, dataset_config)
    if update:
        if not updated_config:
            return []
        else:
            dataset_config = updated_config

    """ Loop over each dataset in config file """
    dataset_ids = []
    for dataset_name, items in dataset_config.items():
        dataset_address = items.get('dataset_address')
        preproc_address = items.get('preproc_address')
        local_path = items.get('path')
        if not (local_path or dataset_address):
            raise Exception("Must provide path or remote address to dataset.")

        if local_path:
            local_path = Path(local_path).absolute().as_posix()

        install_path = local_path or \
            (Path(current_app.config['DATASET_DIR']) / dataset_name).absolute(
                ).as_posix()

        for task_name, params in items['tasks'].items():
            """ Add task to database"""
            dp = dict(params.get('filters', {}).items() | \
                      params.get('ingest_args', {}).items())

            dataset_id = add_task(db_session, task_name,
                                  dataset_name=dataset_name,
                                  local_path=local_path,
                                  dataset_address=dataset_address,
                                  automagic=automagic,
                                  install_path=install_path,
                                  preproc_address=preproc_address,
            					  **dp)
            dataset_ids.append(dataset_id)
            dataset_name = Dataset.query.filter_by(id=dataset_id).one().name

            """ Convert stimuli """
            converters = params.get('converters', None)

            if converters is None:
                converters = all_transformers['converters']
            if converters:
                convert_stimuli(db_session, dataset_name, task_name,
                                         converters, automagic=automagic)

            """ Extract features from applicable stimuli """
            extractors = params.get('extractors', None)

            if extractors is None:
                extractors = all_transformers['extractors']

            if extractors:
                extract_features(db_session, dataset_name, task_name,
                                          extractors, automagic=automagic,
                                          **params.get('extract_args',{}))

    return dataset_ids
