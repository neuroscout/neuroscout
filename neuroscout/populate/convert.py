""" Stimulus conversion.
To apply pliers converters to create new stimuli from original dataset stims.
"""
from flask import current_app
from ..database import db
from pathlib import Path

from pliers.stimuli import (TextStim, ImageStim, VideoFrameStim,
                            ComplexTextStim, VideoStim, AudioStim, load_stims)
from pliers.graph import Graph

from ..models import (
    Dataset, Task, Run, Stimulus, RunStimulus, Predictor, PredictorEvent)
from ..utils.core import listify
from .utils import hash_stim
from .ingest import add_stimulus

import pandas as pd
from tqdm import tqdm
from collections import namedtuple


def save_stim_filename(stimulus):
    """ Given a pliers stimulus object, create a hash, filename, and save.
        If type if TextStim or ComplexTextStim, return content rather than path
    """
    if isinstance(stimulus, TextStim):
        stimulus = ComplexTextStim(text=stimulus.data, onset=stimulus.onset,
                                   duration=stimulus.duration)

    stim_hash = hash_stim(stimulus)

    if isinstance(stimulus, ComplexTextStim):
        return stim_hash, None, stimulus.data, stimulus.name
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

        return stim_hash, path, None, None


def create_new_stimuli(dataset_id, task_name, new_stims, rs_orig, parent_id=None,
                       transformer=None, transformer_params=None, delete_old=True):
    """ Create new derived stimuli and insert into the database
    Args:
        dataset_id - Dataset id.
        task_name - Task name.
        new_stims - List of Pliers stimuli object to insert
        rs_orig - RunStimulus associations of parent stimuli
        parent_id - Optional parent_id
        transfer - Optional transformer to annotate in db
        transformer_params - Parameters to record in db
        delete_old - Deletes old RunStimulus associated with derived stimulus
    """
    new_models = {}
    print("Creating stimuli...")
    for stim in tqdm(new_stims):
        stim_hash, path, content, stim_name = save_stim_filename(stim)

        stim_model, stims = new_models.get(stim_hash, (None, []))

        if stim_model is None:
            mimetype = 'text/csv' if stim_name == 'FULL_TRANSCRIPT' else None
            # Create stimulus model
            stim_model, new = add_stimulus(
                stim_hash, path=path, content=content, parent_id=parent_id,
                converter_name=transformer,
                converter_params=transformer_params,
                dataset_id=dataset_id,
                mimetype=mimetype)

            if delete_old and not new:
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

    converters = [Graph(n) for n in converters]

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
        for graph in converters:
            results = []
            # Extract and flatten results (to a single unit)
            conv = graph.roots[0].transformer
            if conv._stim_matches_input_types(loaded_stim):
                cstim = graph.transform(loaded_stim, merge=False)
                if len(cstim) == 1:
                    cstim = cstim[0]
                params = str(conv.__dict__)
                name = conv.name
                try:  # Add iterable
                    results += cstim
                except TypeError:
                    if hasattr(cstim, 'elements'):
                        results += cstim.elements
                    else:
                        results.append(cstim)

                results = [res for res in results
                           if hasattr(res, 'data') and res.data != '']
                new_stims += create_new_stimuli(
                    dataset_id, task_name, results, rs_orig,
                    parent_id=stim.id,
                    transformer=name,
                    transformer_params=params)

        # De-activate previously generated stimuli from these converters.
        update = Stimulus.query.filter_by(parent_id=stim.id).filter(
            Stimulus.id.notin_(new_stims),
            Stimulus.converter_name == conv.name,
            Stimulus.converter_parameters == str(conv.__dict__))
        if update.count():
            update.update(dict(active=False), synchronize_session='fetch')
        db.session.commit()
        total_new_stims += new_stims

    return total_new_stims


def ingest_text_stimuli(filename, dataset_name, task_name, parent_ids=None,
                        transformer='FAVEAlign', params=None, onsets=None,
                        resample_ratio=1, complete_only=False, col_name='text'):
    """ Ingest converted text stimuli from file.
    Args:
        filename - aligned transcript, with onset, duration and text columns
        dataset_name - Name of dataset in debug
        task_name - Task name
        parent_ids - Parent stimulus db id(s)
        transformer - Transformer name
        params - Extra parameters to recordings
        onsets - onset of the parent stimulus relative to the transcript.
        resample_ratio - Ratio to multiply onsets (after cropping) to adjust
                         for variable play speeds.
        complete_only - Only add complete transcript ComplexTextStim
    """
    dataset_id = Dataset.query.filter_by(name=dataset_name).one().id

    # If no parent ids, find closest matching stimulus
    if parent_ids is None:
        stem = Path(filename).stem
        parent_ids = Stimulus.query.filter_by(
            dataset_id=dataset_id).filter(
                Stimulus.path.contains(stem + ".")).order_by(
                    Stimulus.id.asc()).first().id

    parent_ids = listify(parent_ids)
    onsets = listify(onsets)
    if params is None:
        params = {}

    df = pd.read_csv(filename, delimiter='\t').dropna()

    if onsets is None:
        onsets = [0] * len(parent_ids)
    if len(parent_ids) != len(onsets):
        raise ValueError("parent_ids must match number of onsets")

    for onset, parent_id in zip(onsets, parent_ids):
        # Trim and align trancript
        sub = df[df.onset > onset]
        sub = sub[sub.duration > 0]
        sub['onset'] = (sub['onset'] - onset) * resample_ratio

        # Calculate run duration
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
            TextStim(text=row['text'], onset=row['onset'],
                     duration=row.get('duration'))
            for ix, row in sub.iterrows()]

        # Complete transcript stimulus stand in
        transcript_stim = ComplexTextStim(
            elements=new_stims)
        transcript_stim.name = 'FULL_TRANSCRIPT'

        if complete_only:
            new_stims = [transcript_stim]
        else:
            new_stims.append(transcript_stim)

        params['onset'] = onset
        params['duration'] = duration
        params['resample_ratio'] = resample_ratio

        create_new_stimuli(
            dataset_id, task_name, new_stims, rs_orig,
            parent_id=parent_id, transformer=transformer, 
            transformer_params=params)


def predictor_to_text_stim(predictor_id, task_name, transformer='reading',
                           params=None):
    """ Convert Predictors that were ingested from the original dataset's
    event files into a Stimulus. This is useful for Predictors which are
    speech or reading transcripts with word specific onsets and durations """

    predictor = Predictor.query.filter_by(id=predictor_id).one()
    dataset_id = predictor.dataset_id

    rst = namedtuple('RunStimulus', ['onset', 'duration', 'run_id'])

    if params is None:
        params = {}

    for pr in predictor.predictor_run:
        pes = PredictorEvent.query.filter_by(
            run_id=pr.run_id, predictor_id=predictor_id)

        # Uniquify
        pes = [(pe.value, pe.onset, pe.duration) for pe in pes]
        pes = set(pes)

        # Calculate run duration
        duration = Run.query.filter_by(id=pr.run_id).one().duration

        # Create new stimuli
        new_stims = [
            TextStim(text=pe[0], onset=pe[1],
                     duration=pe[2])
            for pe in pes]

        # Complete transcript stimulus stand in
        transcript_stim = ComplexTextStim(
            elements=new_stims)
        transcript_stim.name = 'FULL_TRANSCRIPT'

        new_stims.append(transcript_stim)

        onset = 0

        # Duration is the max onset + that duration
        duration = max([pe[1] for pe in pes])
        duration += [pe[2] for pe in pes if pe[1] == duration][0]

        rs = rst(onset=onset, duration=duration, run_id=pr.run_id)

        params['onset'] = onset
        params['duration'] = duration

        create_new_stimuli(
            dataset_id, task_name, new_stims, [rs],
            transformer=transformer, transformer_params=params,
            delete_old=False)
