"""
    Mail sending functionality using flask_mail.
"""
from flask import render_template, current_app
from flask_mail import Message
from .core import mail

def send_confirm_mail(recipient, name, confirmation_link):
    """Send account confirmation email
    :param recipient: Email recipient
    :param confirmation_link: The reset link to send
    """

    msg = Message("Welcome to Neuroscout!",
                  recipients=[recipient])
    current_app.logger.info(confirmation_link)
    msg.html = render_template('welcome_email.html',
                               action_url=confirmation_link,
                               name=name,
                               support_email='delavega@utexas.edu')
    mail.send(msg)

def send_reset_mail(recipient, token, name):
    """Send a password reset email
    :param recipient: Email recipient
    :param token: The password reset token
    """

    msg = Message("Neuroscout password reset",
                  recipients=[recipient])

    msg.html = render_template('password_reset.html',
                               token=token,
                               name=name,
                               support_email='delavega@utexas.edu')

    mail.send(msg)
