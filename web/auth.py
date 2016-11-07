from models.auth import user_datastore
from flask_security.utils import verify_password

# JWT Token authentication
def authenticate(username, password):
    user = user_datastore.find_user(email=username)
    if user and username == user.email and verify_password(password, user.password):
        return user
    return None

def load_user(payload):
    user = user_datastore.find_user(id=payload['identity'])
    return user

