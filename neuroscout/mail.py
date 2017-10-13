"""
    Mail sending functionality using flask_mail.
"""
from flask_mail import Message
from core import mail

def send_confirm_mail(recipient, confirmation_link):
    """Send an email via the Flask-Mail extension.
    :param recipient: Email recipient
    :param confirmation_link: The reset link to send
    """

    msg = Message("Welcome to Neuroscout!",
                  recipients=[recipient])
    msg.html = "<a href={}>Confirm account</a>".format(confirmation_link)
    mail.send(msg)

def send_reset_mail(recipient, token):
    """Send an email via the Flask-Mail extension.
    :param recipient: Email recipient
    :param token: The password reset token
    """

    msg = Message("Password reset token",
                  recipients=[recipient])

    if token is None:
        msg.html = "This account doesn't exist!"
    else:
        msg.html = "Reset token: {}".format(token)

    mail.send(msg)
