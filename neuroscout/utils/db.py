"""
    Misc utils related to database functions.
"""
from flask import abort, current_app
from sqlalchemy.exc import SQLAlchemyError
from ..models import Analysis
from ..database import db
from sqlalchemy.event import listens_for
from sqlalchemy.dialects import postgresql
from hashids import Hashids


def dump_pe(pes):
    """ Serialize PredictorEvents, with *SPEED*, using core SQL.
    Warning: relies on attributes being in correct order. """
    statement = str(pes.statement.compile(dialect=postgresql.dialect()))
    params = pes.statement.compile(dialect=postgresql.dialect()).params
    res = db.session.connection().execute(statement, params)
    return [{
      'id': r[0],
      'onset': r[1],
      'duration': r[2],
      'value':  r[3],
      'run_id': r[5],
      'predictor_id': r[6]
      } for r in res]


@listens_for(Analysis, "after_insert")
def update_hash(mapper, connection, target):
    analysis_table = mapper.local_table
    connection.execute(
         analysis_table.update().
         values(
             hash_id=Hashids(
                 current_app.config['HASH_SALT'], min_length=5).
             encode(target.id)).where(analysis_table.c.id == target.id)
    )


def put_record(updated_values, instance, commit=True):
    try:
        for key, value in updated_values.items():
            setattr(instance, key, value)
            if commit is True:
                db.session.commit()
        return instance

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
