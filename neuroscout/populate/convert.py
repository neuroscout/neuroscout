""" Stimulus conversion.
To apply pliers converters to create new stimuli from original dataset stims.
"""
from os.path import join, dirname
from os import makedirs
from flask import current_app
from pathlib import Path

from pliers.stimuli import load_stims
from pliers.stimuli import (TextStim, ImageStim, VideoFrameStim,
                            VideoStim, AudioStim)
from pliers.transformers import get_transformer
from datalad import api as da

from models import Dataset, Task, Run, Stimulus, RunStimulus

from .utils import hash_stim
from .ingest import add_stimulus

def save_stim_filename(stimulus, basepath=''):
    """ Given a pliers stimulus object, create a hash, filename, and save """
    stim_hash = hash_stim(stimulus)

    stim_types = {ImageStim: '.png',
                  TextStim: '.txt',
                  VideoFrameStim: '.png',
                  VideoStim: '.mkv',
                  AudioStim: '.wav'}

    ext = [e for c, e in stim_types.items() if isinstance(stimulus, c)][0]
    filename = join(basepath, stim_hash + ext)

    makedirs(dirname(filename), exist_ok=True)
    stimulus.save(filename)

    return stim_hash, filename

def convert_stimuli(db_session, dataset_name, task_name, converters,
                     verbose=True, automagic=False):
    """ Extract features using pliers for a dataset/task
        Args:
            db_session - database session object
            dataset_name - dataset name
            task_name - task name
            converters - dictionary of converter names to parameters
            verbose - verbose output
            automagic - enable Datalad
        Output:
            list of db ids of converted stimuli
    """
    print("Converting stims")

    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id
    converters = [get_transformer(n, **p) for n, p in converters]

    # Load all active original stimuli for task
    stim_objects = Stimulus.query.filter_by(active=True, parent_id=None).join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name)

    # Datalad unlock all stim paths
    if automagic:
        stim_paths = [s.path for s in stim_objects]
        da.get(stim_paths)
        da.unlock(stim_paths)

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
                    # Save stim to file
                    stim_hash, path = save_stim_filename(res, basepath=Path(
                        current_app.config['STIMULUS_DIR']).absolute().as_posix())

                    # Create stimulus model
                    new_stim, new = add_stimulus(
                        db_session, path, stim_hash, parent_id=stim.id,
                        converter_name=converted.history.transformer_class,
                        converter_params=converted.history.transformer_params,
                        dataset_id=dataset_id)
                    new_stims.append(new_stim.id)

                    if not new:
                        # Delete previous RS associations with this derived stim
                        to_delete = db_session.query(RunStimulus.id).filter_by(
                            stimulus_id=new_stim.id).join(Run).join(
                                Task).filter_by(name=task_name)
                        RunStimulus.query.filter(RunStimulus.id.in_(to_delete)).\
                            delete(synchronize_session='fetch')

                    for rs in rs_orig:
                        new_rs = RunStimulus(stimulus_id=new_stim.id,
                                             run_id=rs.run_id,
                                             onset=rs.onset + (res.onset or 0),
                                             duration=res.duration or rs.duration)
                        db_session.add(new_rs)
                        db_session.commit()

        # De-activate previously generated stimuli from these converters.
        to_update = Stimulus.query.filter_by(parent_id=stim.id).filter(
            Stimulus.id.notin_(new_stims))
        if to_update.count():
            to_update.update(dict(active=False))
        db_session.commit()
        total_new_stims += new_stims

    return total_new_stims
