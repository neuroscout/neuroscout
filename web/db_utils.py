from flask import abort

def copy_row(model, row, ignored_columns=[]):
    copy = model()

    for col in row.__table__.columns:
        if col.name not in ignored_columns:
            try:
                copy.__setattr__(col.name, getattr(row, col.name))
            except Exception as e:
                print(e)
                continue

    return copy

def get_or_create(session, model, commit=True, **kwargs):
    """ Checks to see if instance of model is in db.
    If not add and commit. If true, return all matches.
    Args:
    session: db session
    model: Model class
    **kwargs: columns to filter by

    Returns:
    (all matching or created instances, if instance is new)
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)

        if commit is True:
            session.commit()

        return instance, True
