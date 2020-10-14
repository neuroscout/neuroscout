"""
    Misc utils related to database functions.
"""
from flask import abort, current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..models import (Analysis, RunStimulus, Predictor, PredictorEvent,
                      ExtractedEvent, Stimulus)
from ..database import db
from sqlalchemy.event import listens_for
from sqlalchemy.dialects import postgresql
import shortuuid


def create_pes(predictors, run_ids=None, stimulus_timing=False):
    """ Create PredictorEvents from EFs """
    all_pes = []
    for pred in predictors:
        ef = pred.extracted_feature
        # For all instances for stimuli in this task's runs
        query = ExtractedEvent.query.filter_by(
            ef_id=ef.id).join(Stimulus).join(
                RunStimulus)

        if run_ids is not None:
            query = query.filter(RunStimulus.run_id.in_(run_ids))

        query = query.with_entities(
            'extracted_event.onset', 'extracted_event.duration',
            'extracted_event.value', 'extracted_event.object_id',
            'extracted_event.stimulus_id', 'run_stimulus.run_id',
            'run_stimulus.onset', 'run_stimulus.duration',
            'stimulus.path')

        for (onset, dur, val, o_id, s_id, run_id, rs_onset, rs_dur, s_path) \
                in query:
            if dur is None:
                dur = rs_dur
            s_path = s_path.split('/')[-1] if s_path else None

            res = dict(
                    onset=(onset or 0) + rs_onset,
                    duration=dur,
                    value=val,
                    run_id=run_id,
                    predictor_id=pred.id,
                    object_id=o_id,
                )

            if stimulus_timing:
                res.update(dict(
                    stimulus_id=s_id,
                    stimulus_onset=rs_onset,
                    stimulus_duration=rs_dur,
                    stimulus_path=s_path
                    )
                )

            all_pes.append(res)
    return all_pes


def dump_pe(pes):
    """ Serialize PredictorEvents, with *SPEED*, using core SQL.
    Warning: relies on attributes being in correct order. """
    statement = str(pes.statement.compile(dialect=postgresql.dialect()))
    params = pes.statement.compile(dialect=postgresql.dialect()).params
    res = db.session.connection().execute(statement, params)
    return [
        dict(
            zip(('id', 'onset', 'duration', 'value', 'object_id', 'run_id',
                 'predictor_id', 'stimulus_id'), r))
        for r in res
        ]


def dump_predictor_events(predictor_ids, run_ids=None, stimulus_timing=False):
    """ Query & serialize PredictorEvents, for both Raw and Extracted
    Predictors (which require creating PEs from EEs)
    """

    # Query Predictors
    all_preds = Predictor.query.filter(Predictor.id.in_(predictor_ids))

    # Separate raw and extracted predictors
    raw_pred_ids = [p.id for p in all_preds.filter_by(ef_id=None)]
    ext_preds = Predictor.query.filter(
        Predictor.id.in_(set(predictor_ids) - set(raw_pred_ids)))

    # Query & dump raw PEs
    pes = PredictorEvent.query.filter(
        (PredictorEvent.predictor_id.in_(raw_pred_ids)))
    if run_ids is not None:
        pes = pes.filter((PredictorEvent.run_id.in_(run_ids)))

    pes = dump_pe(pes)

    # Create & dump Extracted PEs
    pes += create_pes(ext_preds, run_ids, stimulus_timing=stimulus_timing)
    return pes


@listens_for(Analysis, "after_insert")
def update_hash(mapper, connection, target):
    analysis_table = mapper.local_table
    shortuuid.set_alphabet('23456789abcdefghijkmnopqrstuvwxyz')
    new_hash = shortuuid.random(length=5)
    res = connection.execute(
        f"select id from analysis where hash_id='{new_hash}'")

    # Check for clashes and generate new if there is one
    while res.rowcount > 0:
        print('trying again')
        new_hash = shortuuid.ShortUUID().random(length=6)
        res = connection.execute(
            f"select id from analysis where hash_id='{new_hash}'")

    connection.execute(
         analysis_table.update().
         values(
             hash_id=new_hash).where(analysis_table.c.id == target.id)
    )


def put_record(updated_values, instance, commit=True):
    try:
        for key, value in updated_values.items():
            setattr(instance, key, value)
            if commit is True:
                db.session.commit()
        return instance
    except IntegrityError as e:
        current_app.logger.error(e)
        db.session.rollback()
        abort(422, "Error updating field")
    except SQLAlchemyError as e:
        current_app.logger.error(e)
        db.session.rollback()
        abort(400, "Error updating field")


def get_or_create(model, commit=True, **kwargs):
    """ Checks to see if instance of model is in db.
    If not add and commit. If true, return all matches.
    Args:
    db_session: db session
    model: Model class
    **kwargs: columns to filter by

    Returns:
    (first matching or created instance, if instance is new)
    """
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)

        if commit is True:
            db.session.commit()

        return instance, True
