from flask_jwt import jwt_required
from flask_apispec import doc
def auth_required(function):
    @doc(params={"authorization": {
    "in": "header", "required": True,
    "description": "Format:  JWT {authorization_token}"}})
    @jwt_required()
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper

def abort(code, message=''):
    from flask import abort, make_response, jsonify
    abort(make_response(jsonify(message=message), code))
