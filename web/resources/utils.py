from flask_jwt import jwt_required, current_identity
from flask_apispec import doc
from webargs.flaskparser import parser
from flask import jsonify
from models import Analysis

def abort(code, message=''):
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
        if current_identity.active is False:
            return abort(
                401, {"message" : "Your account has been disabled."})
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
                401, {"message" : "You are not the owner of this analysis."})

        return function(*args, **kwargs)
    return wrapper

@parser.error_handler
def handle_request_parsing_error(err):
	code, msg = getattr(err, 'status_code', 400), getattr(err, 'messages', 'Invalid Request')
	abort(code, msg)
