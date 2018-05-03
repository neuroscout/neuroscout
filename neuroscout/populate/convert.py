""" Stimulus conversion.
To apply pliers converters to create new stimuli from original dataset stims.
"""
from flask import current_app
from database import db
from pathlib import Path

from pliers.stimuli import (TextStim, ImageStim, VideoFrameStim,
                            VideoStim, AudioStim, load_stims)
from pliers.transformers import get_transformer

from models import Dataset, Task, Run, Stimulus, RunStimulus

from .utils import hash_stim, hash_data
from .ingest import add_stimulus

import pandas as pd

def save_stim_filename(stimulus):
    """ Given a pliers stimulus object, create a hash, filename, and save """
    basepath = Path(current_app.config['STIMULUS_DIR']).absolute()
    stim_hash = hash_stim(stimulus)

    stim_types = {ImageStim: '.png',
                  TextStim: '.txt',
                  VideoFrameStim: '.png',
                  VideoStim: '.mkv',
                  AudioStim: '.wav'}

    ext = [e for c, e in stim_types.items() if isinstance(stimulus, c)][0]
    filename = (basepath / stim_hash).with_suffix(ext)

    filename.parents[0].mkdir(exist_ok=True)
    stimulus.save(filename.as_posix())

    return stim_hash, filename

def save_new_stimulus(dataset_id, task_name, parent_id, rs_orig, stim_hash,
                      transformer=None, transformer_params=None,
                      path=None, content=None, onset=None, duration=None):
    # Create stimulus model
    new_stim, new = add_stimulus(
        stim_hash, path=path, content=content, parent_id=parent_id,
        converter_name=transformer,
        converter_params=transformer_params,
        dataset_id=dataset_id)

    if not new:
        # Delete previous RS associations with this derived stim
        delete = db.session.query(RunStimulus.id).filter_by(
            stimulus_id=new_stim.id).join(Run).join(
                Task).filter_by(name=task_name)
        RunStimulus.query.filter(RunStimulus.id.in_(delete)).\
            delete(synchronize_session='fetch')

    # Create new run stimulus associations
    for rs in rs_orig:
        new_rs = RunStimulus(stimulus_id=new_stim.id,
                             run_id=rs.run_id,
                             onset=rs.onset + (onset or 0),
                             duration=duration or rs.duration)
        db.session.add(new_rs)
        db.session.commit()

    return new_stim.id

def convert_stimuli(dataset_name, task_name, converters):
    """ Extract features using pliers for a dataset/task
        Args:
            dataset_name - dataset name
            task_name - task name
            converters - dictionary of converter names to parameters
        Output:
            list of db ids of converted stimuli
    """
    current_app.logger.info("Converting stimuli")

    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id

    converters = [get_transformer(n, **p) for n, p in converters]

    # Load all active original stimuli for task
    stim_objects = Stimulus.query.filter_by(active=True, parent_id=None).join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    total_new_stims = []
    # Extract new stimuli from original stimuli
    for stim in stim_objects:
        new_stims = []
        # Re-create new RS associations with newly created stims
        rs_orig = RunStimulus.query.filter_by(stimulus_id=stim.id).join(
            Run).join(Task).filter_by(name=task_name)
        loaded_stim = load_stims(stim.path)

        # Extract for each converter
        for conv in converters:
            results = []
            # Extract and flatten results (to a single unit)
            if conv._stim_matches_input_types(loaded_stim):
                converted = conv.transform(loaded_stim)
                try: # Add iterable
                    results += converted
                except TypeError:
                    if hasattr(converted, 'elements'):
                        results += converted.elements
                    else:
                        results.append(converted)

            for res in results:
                # Save stim
                if hasattr(res, 'data') and res.data is not '':
                    if isinstance(res, TextStim):
                        stim_hash = hash_stim(res)
                        content = res.data
                        path = None
                    else:
                        stim_hash, path = save_stim_filename(res)
                        content = None

                    new_stims.append(
                        save_new_stimulus(
                            dataset_id, task_name, stim.id, rs_orig, stim_hash,
                            transformer=converted.history.transformer_class,
                            transformer_params=converted.history.transformer_params,
                            content=content, path=path, onset=res.onset,
                            duration=res.duration))

        # De-activate previously generated stimuli from these converters.
        update = Stimulus.query.filter_by(parent_id=stim.id).filter(
            Stimulus.id.notin_(new_stims),
            Stimulus.converter_name==converted.history.transformer_class,
            Stimulus.converter_parameters==converted.history.transformer_params)
        if update.count():
            update.update(dict(active=False), synchronize_session='fetch')
        db.session.commit()
        total_new_stims += new_stims

    return total_new_stims

def ingest_text_stimuli(filename, dataset_name, task_name, parent_id,
                        transformer, transformer_params=None):
    """ Ingest converted text stimuli from file. """
    ## This ingests from a single parents. May want to refactor in the future
    ## For more complex files (e.g. multiple parents)
    df = pd.read_csv(filename, delimiter='\t')
    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id

    ## Get associations with parent stimulus
    rs_orig = RunStimulus.query.filter_by(stimulus_id=parent_id).join(
        Run).join(Task).filter_by(name=task_name)

    if not rs_orig.count():
        raise Exception("No RunStimulus associations match.")

    for ix, row in df.iterrows():
        stim_hash = hash_data(row['text'])
        save_new_stimulus(dataset_id, task_name, parent_id, rs_orig, stim_hash,
                          transformer=transformer,
                          transformer_params=transformer_params,
                          content=row['text'], onset=row['onset'],
                          duration=row.get('duration'))
