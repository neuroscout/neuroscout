""" Utilities that don't touch flask """


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
