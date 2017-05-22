from flask_jwt import jwt_required, current_identity
from flask_apispec import doc
from webargs.flaskparser import parser
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app

def auth_required(function):
    @doc(params={"authorization": {
    "in": "header", "required": True,
    "description": "Format:  JWT {authorization_token}"}})
    @jwt_required()
    def wrapper(*args, **kwargs):
        if current_identity.active is False:
            return jsonify({"message" : "Your account has been disabled."})
        return function(*args, **kwargs)
    return wrapper

def abort(code, message=''):
    from flask import abort, make_response, jsonify
    abort(make_response(jsonify(message=message), code))

@parser.error_handler
def handle_request_parsing_error(err):
    print(err)
    code, msg = getattr(err, 'status_code', 400), getattr(err, 'messages', 'Invalid Request')
    abort(code, msg)

def first_or_404(query):
    first = query.first()
    if first:
        return first
    else:
        abort(404, 'Resource not found')

def put_record(session, updated_values, instance):
    try:
        for key, value in updated_values.items():
            setattr(instance, key, value)
            session.commit()
        return instance

    except SQLAlchemyError as e:
        current_app.logger.error(e)
        session.rollback()
        abort(400, "Error updating field")
