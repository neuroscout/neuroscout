""" Stimulus conversion.
To apply pliers converters to create new stimuli from original dataset stims
"""
from pliers.stimuli import load_stims
import pliers.converters

from datalad import api as da

from flask import current_app

from .utils import hash_data

from models import Dataset, Task, Run, Stimulus, RunStimulus
from .ingest import create_stimulus
from os.path import join

from pliers.stimuli import (TextStim, ImageStim, VideoFrameStim,
                            VideoStim, AudioStim)

def save_stim_filename(stimulus, basepath=''):
    """ Given a pliers stimulus object, created hash, filename, and save """
    stim_hash = hash_data(stimulus.data)

    stim_types = {ImageStim: '.png',
                  TextStim: '.txt',
                  VideoFrameStim: '.png',
                  VideoStim: '.mkv',
                  AudioStim: '.wav'}

    ext = [e for c, e in stim_types.items() if isinstance(stimulus, c)][0]
    filename = join(basepath, stim_hash + ext)

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

    def load_converter(converter_name, parameters):
        if hasattr(pliers.converters, converter_name):
            conv = getattr(pliers.converters, converter_name)(**parameters)
        else:
            conv = getattr(pliers.filters, converter_name)(**parameters)
        return conv

    # Load converters
    converters = [load_converter(n, p) for n, p in converters.items()]

    # Load all active original stimuli for task
    stim_objects = Stimulus.query.filter_by(active=True, parent_id=None).join(
        RunStimulus).join(Run).join(Task).filter_by(name=task_name).join(
            Dataset).filter_by(name=dataset_name).all()

    # TODO:
    # For all converters, disable sitmuli generated with those converters previously
    # (for updating)
    # Also disbale RunStimulus record to only apply to featues about to generated
    # Finally, how to selectively disbale some stimuli (e.g. german ones)

    # Datalad unlock all stim paths
    if automagic:
        stim_paths = [s.path for s in stim_objects]
        da.get(stim_paths)
        da.unlock(stim_paths)

    # Loop over original stimuli in db
    for stim in stim_objects:
        results = []
        loaded_stim = load_stims(stim.path)

        # Extract for each converter
        for conv in converters:
            if conv._stim_matches_input_types(loaded_stim):
                res = conv.transform(loaded_stim)
                try: # Add iterable
                    results += res
                except TypeError:
                    if hasattr(res, 'elements'):
                        results += res.elements
                    else:
                        results.append(res)

        rs_orig = RunStimulus.query.filter_by(stimulus_id=stim.id).join(
            Run).join(Task).filter_by(name=task_name).all()

        for res in results:
            if res.data:
                # Save stim to file
                stim_hash, path = save_stim_filename(
                    res, basepath=current_app.config['STIMULUS_DIR'])

                # Create stimulus model
                new_model, new = create_stimulus(
                    db_session, path, stim_hash, parent_id=stim.id,
                    converter_name=res.history.transformer_class,
                    converter_params=res.history.transformer_params)

                if res.onset is None:
                    res.onset = 0

                # Create new RS associations
                for rs in rs_orig:
                    duration = rs.duration if res.duration is None \
                               else res.duration

                    new_rs = RunStimulus(stimulus_id=new_model.id,
                                         run_id=rs.run_id,
                                         onset=rs.onset+res.onset,
                                         duration=duration)
                    db_session.add(new_rs)
                    db_session.commit()
