""" Auth related functions """
from models.auth import user_datastore, User
from flask_security.utils import verify_password
from flask_security.confirmable import generate_confirmation_token
from flask_security.recoverable import generate_reset_password_token
from flask import current_app, url_for
from mail import send_confirm_mail, send_reset_mail

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

    send_reset_mail(email, token)

def register_user(**kwargs):
    """ Register new user and password """
    confirmation_link, token = None, None
    user = user_datastore.create_user(**kwargs)
    user_datastore.commit()

    if current_app.config['CONFIRM_USERS']:
        confirmation_link, token = generate_confirmation_link(user)

    if current_app.config['SEND_REGISTER_EMAIL']:
        send_confirm_mail(user.email, confirmation_link)

    return user

# JWT Token authentication
def authenticate(username, password):
    """ Authenticate user and password combination """
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
