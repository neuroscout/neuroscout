from flask import jsonify, request
from flask_jwt import jwt_required, current_identity
from flask_apispec import doc
import datetime
from webargs.flaskparser import parser
from ..models import Analysis
from ..database import db
from marshmallow import ValidationError


def abort(code, message=''):
    """ JSONified abort """
    from flask import abort, make_response
    abort(make_response(jsonify(message=message), code))


def first_or_404(query):
    """ Return first instance of query or throw a 404 error """
    first = query.first()
    if first:
        return first
    else:
        abort(404, 'Resource not found')


def fetch_analysis(function):
    """ Given kwarg analysis_id, fetch analysis model and insert as kwargs """
    def wrapper(*args, **kwargs):
        analysis = first_or_404(
            Analysis.query.filter_by(hash_id=kwargs.pop('analysis_id')))
        kwargs['analysis'] = analysis
        return function(*args, **kwargs)
    return wrapper


def auth_required(function):
    """" A valid JWT is required to access """
    @doc(params={"authorization": {
        "in": "header", "required": True,
        "description": "Format:  JWT {authorization_token}"}})
    @jwt_required()
    def wrapper(*args, **kwargs):
        # Record activity time and IP
        if (current_identity.first_login and
           current_identity.last_activity_at is not None):
            current_identity.first_login = False
        current_identity.last_activity_at = datetime.datetime.now()
        current_identity.last_activity_ip = request.environ['REMOTE_ADDR']
        db.session.commit()

        if current_identity.active is False:
            return abort(
                401, "Your account has been disabled.")
        elif current_identity.confirmed_at is None:
            return abort(
                401, "Your account has not been confirmed.")

        return function(*args, **kwargs)
    return wrapper


def owner_required(function):
    """ A JWT matching the user id of the analysis is required,
        assumes analysis id is second argument, and replaces id with
        Analysis object if succesfull. """
    @auth_required
    @fetch_analysis
    def wrapper(*args, **kwargs):
        if current_identity.id != kwargs['analysis'].user_id:
            return abort(
                404, {"message": "Resource not found."})
        return function(*args, **kwargs)
    return wrapper


@parser.error_handler
def handle_request_parsing_error(error, req, schema, error_status_code,
                                 error_headers):
    if isinstance(error, ValidationError):
        code = 422
    else:
        code = error_status_code or 400
    msg = error.messages or 'Invalid request'
    abort(code, msg)
