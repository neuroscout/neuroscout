import json
from flask import current_app
from .ingest import add_task
from .extract import extract_features
from .convert import convert_stimuli
from models import Dataset
from pathlib import Path
from pliers.utils.updater import check_updates
import itertools

def load_update_config(db_session, config_file, update=False):
    """ Returns element of config file that must be re-extracted
        as well as prepopulating default transformers in config file. """
    config_dict =  json.load(open(config_file, 'r'))

    default_tfs = json.load(
        open(current_app.config['ALL_TRANSFORMERS'], 'r'))

    tfs = []
    for _, dataset in config_dict.items():
        for _, task in dataset['tasks'].items():
         task['extractors'] = task.get('extractors', default_tfs['extractors'])
         task['converters'] = task.get('converters', default_tfs['converters'])

         tfs += task['extractors'] + task['converters']

    tfs = list(k for k,_ in itertools.groupby(tfs)) # Unique-ify

    # Check for updates
    datastore = Path(current_app.config['FEATURE_DATASTORE'])
    datastore.parents[0].mkdir(exist_ok=True)
    updated = check_updates(tfs, datastore=datastore.as_posix())

    if update:
        # Filter configs to only include updated transformers
        filt_config = {}
        for dname, dataset in config_dict.items():
            new_tasks = {}
            for tname, task in dataset.pop('tasks').items():
                filt_ext = [e for e in task['extractors'] \
                            if tuple(e) in updated['transformers']]
                filt_conv = [c for c in task['converters'] \
                            if tuple(c) in updated['transformers']]

                if filt_ext or filt_conv:
                    task['extractors'] = filt_ext
                    task['converters'] = filt_conv
                    new_tasks[tname] = task

            if new_tasks:
                dataset['tasks'] = new_tasks
                filt_config[dname] = dataset

        config_dict = filt_config

    return config_dict

def ingest_from_json(db_session, config_file, automagic=False,
                     update_features=False, reingest=False):
    """ Adds a datasets from a JSON configuration file
        Args:
            db_session - sqlalchemy db db_session
            config_file - a path to a json file
            automagic - force enable DataLad automagic
            update_features - re-extracted updated extractors
            reingest - force reingest dataset
        Output:
            list of dataset model ids
     """
    dataset_config = load_update_config(db_session, config_file,
                                      update=update_features)
    if update_features:
        if not (dataset_config or reingest):
            return []

    """ Loop over each dataset in config file """
    dataset_ids = []
    for dataset_name, items in dataset_config.items():
        dataset_address = items.get('dataset_address')
        preproc_address = items.get('preproc_address')
        local_path = items.get('path')

        if local_path:
            local_path = Path(local_path).absolute().as_posix()
        elif not dataset_address:
            raise Exception("Must provide path or remote address to dataset.")

        for task_name, params in items['tasks'].items():
            """ Add task to database"""
            dp = params.get('ingest_args', {})
            dp.update(params.get('filters', {}))

            dataset_id = add_task(db_session, task_name,
                                  dataset_name=dataset_name,
                                  local_path=local_path,
                                  dataset_address=dataset_address,
                                  automagic=automagic,
                                  preproc_address=preproc_address,
                                  reingest=reingest,
            					  **dp)
            dataset_ids.append(dataset_id)
            dataset_name = Dataset.query.filter_by(id=dataset_id).one().name

            """ Convert stimuli """
            converters = params.get('converters', None)
            if converters:
                convert_stimuli(db_session, dataset_name, task_name, converters)

            """ Extract features from applicable stimuli """
            extractors = params.get('extractors', None)
            if extractors:
                extract_features(db_session, dataset_name, task_name,
                                 extractors, **params.get('extract_args',{}))
    return dataset_ids
