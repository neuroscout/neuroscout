"""
    Misc utils related to database functions.
"""
from flask import abort, current_app
from sqlalchemy.exc import SQLAlchemyError
from ..models import db, Analysis
from sqlalchemy.event import listens_for
from hashids import Hashids


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
