import json
import shutil
from os import symlink
from flask import current_app
from .ingest import add_task
from .extract import extract_features, extract_tokenized_features
from .convert import convert_stimuli
from .transform import Postprocessing
from pathlib import Path
from datalad.api import install
from datalad.distribution.utils import _get_installationpath_from_url
from bids.layout import BIDSLayout


def setup_dataset(preproc_address, dataset_address=None, dataset_path=None,
                  setup_preproc=True, url=None, summary=None, 
                  long_description=None, tasks=None):
    """ Installs Dataset (if a dataset_path is not given), and configures it.
    Sets up a template JSON for the dataset for subequent ingestion. """

    if dataset_path is None:
        if dataset_address is None:
            raise ValueError(
                "Either dataset_path or dataset_address must be specified.")
        else:
            # Find unique folder name
            dataset_name = _get_installationpath_from_url(dataset_address)
            path = Path('/datasets/raw') / dataset_name
            if path.exists():
                iter = 1
                while path.exists():
                    iter += 1
                    path = Path('/datasets/raw') / f"{dataset_name}_{iter}"

            dataset_name = path.stem

            # Install dataset
            dataset_path = install(
                source=dataset_address,
                path=str(path)
                ).path

    if setup_preproc:
        # Clone preproc dataset
        preproc_dataset_name = _get_installationpath_from_url(preproc_address)
        preproc_path = Path("/datasets/neuroscout-datasets")

        # If no container folder for preproc, add one
        if preproc_dataset_name in ['fmriprep', 'preproc']:
            preproc_path = preproc_path / f"{dataset_name}"

        preproc_path = preproc_path / preproc_dataset_name
        preproc_path.mkdir(parents=True)

        install(
            source=preproc_address,
            path=str(preproc_path)
        )

        # Set preproc path
        if preproc_path.stem not in ['fmriprep', 'preproc']:
            # Assume only directory is preproc dir
            preproc_path = [f for f in preproc_path.iterdir()
                            if not f.name.startswith(".")][0]

        # Reset derivatives folder
        derivatives = Path(dataset_path) / 'derivatives'
        shutil.rmtree(derivatives)

        # Add symlink to derivative in raw dataset
        derivatives.mkdir()
        symlink(str(preproc_path), str(derivatives / preproc_path.stem))

    # Extract dataset summary
    layout = BIDSLayout(path, index_metadata=False)

    # Extract tasks and task summaries
    tasks = {}
    for t in layout.get_tasks():
        try:
            summary = layout.get(task=t, extension='nii.gz')[0].get_metadata()
        except ValueError:
            summary = ""

        tasks[t] = {
            "summary": summary
        }

    # Create template JSON file
    template = {
        "name": dataset_name,
        "dataset_address": dataset_address,
        "preproc_address": preproc_address,
        "path": dataset_path,
        "url": url,
        "summary": summary,
        "long_description": long_description,
        "tasks": tasks
    }

    config_file_path = (current_app.config['CONFIG_PATH'] \
        / 'datasets' / dataset_name).with_suffix('.json')

    json.dump(template, config_file_path.open('w'), indent=4)
    return str(config_file_path)


def _add_dataset():
    pass


def _get_tasks():
    pass


def ingest_from_json(config_file, reingest=False, setup_only=False):
    """ Adds a dataset from a JSON configuration file
        Args:
            config_file - a path to a json file
            reingest - force reingest tasks
            setup_only - Only set up dataset
        Output:
            list of dataset model ids
    """
    if not (config_file or reingest):
        return []

    dataset_address = config_file.get('dataset_address')
    preproc_address = config_file.get('preproc_address')
    dataset_name = config_file.get('name')
    local_path = config_file.get('path')

    if not local_path:
        local_path, dataset_id = _setup_dataset(
            dataset_address, preproc_address, local_path)

    if setup_only:
        return dataset_id

    # Add dataset
    _add_dataset(
        dataset_name=dataset_name,
        dataset_summary=config_file.get('summary'),
        dataset_long_description=config_file.get('long_description'),
        local_path=local_path,
        url=config_file.get('url')
    )

    tasks = config_file['tasks']
    if len(tasks) == 1 and '*' in tasks:
        unique_tasks = _get_tasks(local_path)

    for t in unique_tasks:
        pass  # Set up empty defaul structure

    task_ids = []
    for task_name, params in config_file['tasks'].items():
        """ Add task to database"""
        dp = params.get('ingest_args', {})
        dp.update(params.get('filters', {}))
        task_id = add_task(
            task_name,
            local_path=local_path,
            reingest=reingest,
            task_summary=params.get('summary'),
            **dp)
        task_ids.append(task_id)

        """ Convert stimuli """
        converters = params.get('converters', None)
        if converters:
            print("Converting... {}".format(converters))
            convert_stimuli(dataset_name, task_name, converters)

        """ Extract features from applicable stimuli """
        extractor_graphs = params.get('extractors', None)
        if extractor_graphs:
            print("Extracting...")
            extract_features(
                extractor_graphs, dataset_name, task_name)

        """ Extract features that require pre-tokenization """
        tokenized_extractors = params.get('tokenized_extractors', None)
        if tokenized_extractors:
            print("Tokenizing and extracting... {}".format(
                tokenized_extractors))
            extract_tokenized_features(
                dataset_name, task_name, tokenized_extractors)

        """ Apply transformations """
        transformations = params.get("transformations", [])
        post = Postprocessing(dataset_name, task_name)
        for args in transformations:
            print("Applying transformation... {}".format(args))
            post = Postprocessing(dataset_name, task_name)
            post.apply_transformation(**args)

    return dataset_id
