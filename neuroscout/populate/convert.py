""" Stimulus conversion.
To apply pliers converters to create new stimuli from original dataset stims.
"""
from flask import current_app
from database import db
from pathlib import Path

from pliers.stimuli import (TextStim, ImageStim, VideoFrameStim,
                            ComplexTextStim, VideoStim, AudioStim, load_stims)
from pliers.transformers import get_transformer

from models import Dataset, Task, Run, Stimulus, RunStimulus
from utils.core import listify
from .utils import hash_stim
from .ingest import add_stimulus

import pandas as pd

def save_stim_filename(stimulus):
    """ Given a pliers stimulus object, create a hash, filename, and save.
        If type if TextStim or ComplexTextStim, return content rather than path.
    """
    if isinstance(stimulus, TextStim):
        stimulus = ComplexTextStim(text=stimulus.data)

    stim_hash = hash_stim(stimulus)

    if isinstance(stimulus, ComplexTextStim):
        return stim_hash, None, stimulus.data
    else:
        basepath = Path(current_app.config['STIMULUS_DIR']).absolute()

        stim_types = {ImageStim: '.png',
                      VideoFrameStim: '.png',
                      VideoStim: '.mkv',
                      AudioStim: '.wav'}

        ext = [e for c, e in stim_types.items() if isinstance(stimulus, c)][0]
        path = (basepath / stim_hash).with_suffix(ext)

        path.parents[0].mkdir(exist_ok=True)
        stimulus.save(path.as_posix())

        return stim_hash, path, None

def create_new_stimuli(dataset_id, task_name, parent_id, new_stims, rs_orig,
                       transformer=None, transformer_params=None):
    new_models = {}
    for stim in new_stims:
        stim_hash, path, content = save_stim_filename(stim)

        stim_model, stims = new_models.get(stim_hash, (None, []))

        if stim_model is None:
            # Create stimulus model
            stim_model, new = add_stimulus(
                stim_hash, path=path, content=content, parent_id=parent_id,
                converter_name=transformer,
                converter_params=transformer_params,
                dataset_id=dataset_id)

            if not new:
                # Delete previous RS associations with this derived stim
                delete = db.session.query(RunStimulus.id).filter_by(
                    stimulus_id=stim_model.id).join(Run).join(
                        Task).filter_by(name=task_name)
                RunStimulus.query.filter(RunStimulus.id.in_(delete)).\
                    delete(synchronize_session='fetch')

        stims.append(stim)

        new_models[stim_hash] = (stim_model, stims)

    new_rs = []
    for stim_model, stims in new_models.values():
        for stim in stims:
            for rs in rs_orig:
                new_rs.append(
                    RunStimulus(stimulus_id=stim_model.id,
                                run_id=rs.run_id,
                                onset=rs.onset + (stim.onset or 0),
                                duration=stim.duration or rs.duration)
                    )

    db.session.bulk_save_objects(new_rs)
    db.session.commit()

    return [v[0].id for v in new_models.values()]

def convert_stimuli(dataset_name, task_name, converters):
    """ Convert stimuli to different modality using pliers.
        Args:
            dataset_name - dataset name
            task_name - task name
            converters - dictionary of converter names to parameters
        Output:
            list of db ids of converted stimuli
    """
    print("Converting stimuli")

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

            results = [res for res in results if hasattr(res, 'data') and res.data is not '']
            new_stims = create_new_stimuli(
                dataset_id, task_name, stim.id, results, rs_orig,
                transformer=converted.history.transformer_class,
                transformer_params=converted.history.transformer_params)

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

def ingest_text_stimuli(filename, dataset_name, task_name, parent_ids,
                        transformer='FAVEAlign', params=None, onsets=None,
                        resample_ratio=1):
    """ Ingest converted text stimuli from file.
    Args:
        filename - aligned transcript, with onset, duration and text columns
        dataset_name - Name of dataset in debug
        task_name - Task name
        parent_ids - Parent stimulus db id(s)
        transformer - Transformer name
        params - Extra parameters to recordings
        onsets - onset of the parent stimulus relative to the transcript.
        resample_ratio - Ratio to multiply onsets (after cropping) to adjust for
                         variable play speeds.
    """
    df = pd.read_csv(filename, delimiter='\t')
    parent_ids = listify(parent_ids)
    onsets = listify(onsets)
    if params is None:
        params = {}

    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id

    if onsets is None:
        onsets = [0] * len(parent_ids)
    if len(parent_ids) != len(onsets):
        raise ValueError("parent_ids must match number of onsets")

    for onset, parent_id in zip(onsets, parent_ids):
        # Trim and align trancript
        sub = df[df.onset > onset]
        sub['onset'] = (sub['onset'] - onset) * resample_ratio

        duration = max(db.session.query(RunStimulus.duration).filter_by(
            stimulus_id=parent_id).distinct())[0]
        if onset < 0:
            duration = duration - onset
        sub = sub[sub.onset < duration]

        # Get associations with parent stimulus
        rs_orig = RunStimulus.query.filter_by(stimulus_id=parent_id).join(
            Run).join(Task).filter_by(name=task_name)

        if not rs_orig.count():
            raise Exception("No RunStimulus associations match.")

        # Create new stimuli
        new_stims = [
            ComplexTextStim(text=row['text'], onset=row['onset'],
                            duration=row.get('duration'))
            for ix, row in sub.iterrows()]

        params['onset'] = onset
        params['duration'] = duration
        params['resample_ratio'] = resample_ratio

        create_new_stimuli(
            dataset_id, task_name, parent_id, new_stims, rs_orig,
            transformer=transformer, transformer_params=params)
