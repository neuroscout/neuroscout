""" Auth related functions """
import datetime
from models.auth import user_datastore, User
from flask_security.utils import verify_password
from flask_security.confirmable import generate_confirmation_token
from flask_security.recoverable import generate_reset_password_token
from flask import current_app, url_for
from mail import send_confirm_mail, send_reset_mail
from google.oauth2 import id_token
from google.auth.transport import requests

def generate_confirmation_link(user):
    """ For a given user, generates confirmation link and token.
    Stand-in for flask_security function that requires enabling other
    non-RESTFul confirmation routes """
    # Use generate_confirmation_token to create token
    token = generate_confirmation_token(user)
    return url_for('confirm', token=token, _external=True), token

def reset_password(email):
    """Sends the reset password instructions email for the specified email.
    :param email: The email to send the instructions to
    """
    user = User.query.filter_by(email=email).first()
    token = generate_reset_password_token(user) if user else None
    name = user.name if user else None
    send_reset_mail(email, token, name)

def send_confirmation(user):
    """Attempts to send confirmation email to user. Returns True if performed.
    """
    if current_app.config['SEND_REGISTER_EMAIL'] and \
        user.confirmed_at is None:
        confirmation_link, token = generate_confirmation_link(user)
        send_confirm_mail(user.email, user.name, confirmation_link)

        return True
    else:
        return False

def register_user(**kwargs):
    """ Register new user and password """
    user = user_datastore.create_user(**kwargs)
    user_datastore.commit()
    send_confirmation(user)
    return user

def _authenticate_google(token):
    """ Authenticate google JWT token """
    try:
        ginfo = id_token.verify_oauth2_token(
                token, requests.Request(), current_app.config['GOOGLE_CLIENT_ID'])
        if ginfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        return ginfo

    except ValueError:
        return None

def _find_create_google(ginfo):
    """ Find google user in db, or create new user if none found """
    # Find user Google ID
    user = user_datastore.find_user(google_id=ginfo['sub'])
    if user is not None:
        return user

    # Find using email
    user = user_datastore.find_user(email=ginfo['email'])
    confirmed_at = datetime.datetime.utcnow() if ginfo['email_verified'] else None

    if user is not None:
        if user.confirmed_at is None:
            user.confirmed_at = confirmed_at
        return user

    # Create new user
    user = user_datastore.create_user(
            email=ginfo['email'],
            google_id=ginfo['sub'],
            confirmed_at=confirmed_at)
    user_datastore.commit()

    # Might need to worry about edge cases in which email changes
    return user

def authenticate(username, password):
    """ Authenticate user and password combination
    Returns user object if succesful, otherwise None """
    if username == 'GOOGLE':
        ginfo = _authenticate_google(password)
        if ginfo:
            return _find_create_google(ginfo)
    else:
        user = user_datastore.find_user(email=username)
        if user and username == user.email and verify_password(password, user.password):
            return user
    return None

def load_user(payload):
    """ Load_user function for flask jwt """
    user = user_datastore.find_user(id=payload['identity'])
    return user

def add_auth_to_swagger(spec):
    """ Document auth paths using swagger """
    spec.add_path(
        path='/api/auth',
        operations=dict(
            post=dict(
                parameters=[
                    {
                        "in": "body",
                        "name": "body",
                        "required": True,
                        "schema": {
                            "properties": {"email": {"type": "string"},
                                           "password": {"type": "string"}},
                            "type": "object",
                            "example" : {
                                "email" : "user@example.com",
                                "password" : "string" }}
                        }
                    ],
                tags = ["auth"],
                summary = "Get JWT authorizaton token.",
                responses={
                    "default": {
                        "description": "",
                        "schema": {
                            "properties": {
                                "authorizaton_token": {"type": "string"},
                                "type": "object"
                                }}}})))
