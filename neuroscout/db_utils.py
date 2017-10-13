"""
    Misc utils related to database functions.
"""
from flask import abort, current_app
from sqlalchemy.exc import SQLAlchemyError

def copy_row(model, row, ignored_columns=[], ignored_relationships=[]):
    copy = model()

    for col in row.__table__.columns:
        if col.name not in ignored_columns:
            copy.__setattr__(col.name, getattr(row, col.name))

    # Copy relationships:
    for r in row.__mapper__.relationships:
        if r.key not in ignored_relationships:
            copy.__setattr__(r.key, getattr(row, r.key))
    return copy

def put_record(db_session, updated_values, instance, commit=True):
    try:
        for key, value in updated_values.items():
            setattr(instance, key, value)
            if commit is True:
                db_session.commit()
        return instance

    except SQLAlchemyError as e:
        current_app.logger.error(e)
        db_session.rollback()
        abort(400, "Error updating field")

def get_or_create(db_session, model, commit=True, **kwargs):
    """ Checks to see if instance of model is in db.
    If not add and commit. If true, return all matches.
    Args:
    db_session: db session
    model: Model class
    **kwargs: columns to filter by

    Returns:
    (first matching or created instance, if instance is new)
    """
    instance = db_session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db_session.add(instance)

        if commit is True:
            db_session.commit()

        return instance, True
