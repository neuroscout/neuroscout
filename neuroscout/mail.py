from flask_mail import Message
from core import mail
def send_confirm_mail(recipient, confirmation_link):
    """Send an email via the Flask-Mail extension.
    :param subject: Email subject
    :param recipient: Email recipient
    :param template: The name of the email template
    :param context: The context to render the template with
    """

    msg = Message("Welcome to Neuroscout!",
                  recipients=[recipient])

    # To-do implement email templates
    msg.html = "<a href={}>Confirm account</a>".format(confirmation_link)

    mail.send(msg)
