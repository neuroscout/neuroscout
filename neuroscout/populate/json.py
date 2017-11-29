import json
from pathlib import Path
from .ingest import add_task
from .extract import extract_features
from .convert import convert_stimuli

from models import Dataset

# from pliers.updater import check_updates

# def check_updates_json():
#     """ Checks which converters extractors have been updated in a json"""
#     ft_path = current_app.config['FEATURE_TRACKING_DIR']
#     makedirs(ft_path, exist_ok=True)
#
#     updated_extractors = []
#
#     return updated_extractors

def ingest_from_json(db_session, config_file, install_path='/file-data',
                     automagic=False, update=False):
    dataset_config = json.load(open(config_file, 'r'))

    """ Loop over each dataset in config file """
    dataset_ids = []
    for dataset_name, items in dataset_config.items():
        dataset_address = items.get('dataset_address')
        preproc_address = items.get('preproc_address')
        local_path = items.get('path')
        if not (local_path or dataset_address):
            raise Exception("Must provide path or remote address to dataset.")

        # If dataset is remote link, set install path
        if local_path is None:
            new_path = str((Path(install_path) / dataset_name).absolute())
        else:
            new_path = local_path

        for task_name, params in items['tasks'].items():
            """ Add task to database"""
            dp = dict(params.get('filters', {}).items() | \
                      params.get('ingest_args', {}).items())

            dataset_id = add_task(db_session, task_name,
                                  dataset_name=dataset_name,
                                  local_path=local_path,
                                  dataset_address=dataset_address,
                                  automagic=automagic,
                                  install_path=new_path,
                                  preproc_address=preproc_address,
            					  **dp)
            dataset_ids.append(dataset_id)
            dataset_name = Dataset.query.filter_by(id=dataset_id).one().name

            """ Convert stimuli """
            automagic = local_path is None or automagic
            converters = params.get('converters', {})
            if converters:
                convert_stimuli(db_session, dataset_name, task_name,
                                         converters, automagic=automagic)

            """ Extract features from applicable stimuli """
            extractors = params.get('extractors', {})
            if extractors:
                extract_features(db_session, dataset_name, task_name,
                                          extractors, automagic=automagic,
                                          **params.get('extract_args',{}))

    return dataset_ids
