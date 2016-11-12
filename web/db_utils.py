from sqlalchemy.exc import SQLAlchemyError
from flask_restful import abort

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

def put_record(session, updated_values, instance):
	try:
		for key, value in updated_values.items():
			setattr(instance, key, value)
			session.commit()
			print(key, value)

	except SQLAlchemyError:
		session.rollback()
		abort(400, message="Database error")
