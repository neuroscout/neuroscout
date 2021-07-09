import json
import shutil
from os import symlink
from os.path import relpath
from flask import current_app
from .ingest import add_task, add_dataset
from .extract import extract_features, extract_tokenized_features
from .convert import convert_stimuli
from .transform import Postprocessing
from .utils import add_to_bibliography
from pathlib import Path
from datalad.api import install, get
from datalad.distribution.utils import _get_installationpath_from_url
from bids.layout import BIDSLayout


def setup_dataset(preproc_address, raw_address=None, path=None,
                  skip_preproc=False, url=None, dataset_summary=None,
                  long_description=None, tasks=None, bib_entries=[], **kwargs):
    """ Installs Dataset using DataLad (unless a dataset_path is given),
    links preproc and raw dataset, and creates a template config file
    for the dataset.

    Args:
       preproc_address: DataLad address of a fmripreprocessed dataset
       dataset_address: DataLad address to raw dataset
       path: path on disk to raw BIDS dataset. If provided,
                     `dataset_address` is optional.
       skip_preproc: if False, install preproc remote, add symlink to raw
       url: URL to dataset information
       dataset_summary: Short summary of dataset
       long_description: Longer description of dataset
       tasks: List of tasks to include in config file
       bib_entries: List of bibliography entries in CSL format.
       kwargs: Additional arguments to add to the config file (i.e. filters)

    Returns:
       path to template config_file """

    if path is None:
        if raw_address is None:
            raise ValueError(
                "Either dataset_path or dataset_address must be specified.")
        else:
            # Find unique folder name
            dataset_name = _get_installationpath_from_url(raw_address)
            candidate_path = Path('/datasets/raw') / dataset_name
            if candidate_path.exists():
                iter = 1
                while candidate_path.exists():
                    iter += 1
                    candidate_path = Path('/datasets/raw') / f"{dataset_name}_{iter}"

            # Install dataset
            dataset_path = Path(install(
                source=raw_address,
                path=str(candidate_path)
                ).path)
            get(str(candidate_path / 'dataset_description.json'))

    else:
        dataset_path = Path(path)

    dataset_name = dataset_path.stem

    if not skip_preproc:
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
        derivatives = dataset_path / 'derivatives'
        shutil.rmtree(derivatives)

        # Add relative symlink to derivative in raw dataset
        derivatives.mkdir()
        symlink(relpath(str(preproc_path), str(derivatives)),
                str(derivatives / preproc_path.stem))

    # Extract dataset summary
    layout = BIDSLayout(dataset_path)

    # Extract tasks and task summaries
    tasks = {}
    for t in layout.get_tasks():
        try:
            summary = layout.get(task=t, extension='nii.gz')[0].get_metadata()['TaskDescription']
        except KeyError:
            summary = ""

        tasks[t] = {
            "summary": summary,
            **kwargs
        }

    # Create template JSON file
    template = {
        "name": dataset_name,
        "dataset_address": raw_address,
        "preproc_address": preproc_address,
        "path": str(dataset_path),
        "url": url,
        "summary": dataset_summary,
        "long_description": long_description,
        "tasks": tasks,
        "bib_entries": bib_entries
    }

    config_file_path = (current_app.config['CONFIG_PATH']
                        / 'datasets' / dataset_name).with_suffix('.json')

    with open(config_file_path, 'w') as f:
        json.dump(template, f, indent=4)
    return str(config_file_path)


def ingest_from_json(config_file, reingest=False):
    """ Adds a dataset from a JSON configuration file
        Args:
            config_file - a path to a json file
            reingest - force reingest tasks
        Output:
            list of dataset model ids
    """

    with open(config_file, 'r') as f:
        config = json.load(f)

    dataset_name = config['name']
    local_path = config['path']

    # Add dataset
    dataset_id = add_dataset(
        dataset_name=dataset_name,
        dataset_address=config.get('dataset_address'),
        dataset_summary=config.get('summary'),
        preproc_address=config['preproc_address'],
        dataset_long_description=config.get('long_description'),
        local_path=local_path,
        url=config.get('url'),
        reingest=reingest
    )

    task_ids = []
    for task_name, params in config['tasks'].items():
        """ Add task to database"""
        task_id = add_task(
            task_name,
            dataset_name,
            local_path,
            reingest=reingest,
            **params)
        task_ids.append(task_id)

    # Add bibliography entry
    add_to_bibliography(dataset_name, config['bib_entries'])

    return dataset_id


def extract_from_json(dataset_name, tasks, config):  
    ## TODO: Use list of datasets and tasks to filter candidate tasks, and then apply to all

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