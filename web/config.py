import os

class Config(object):
    DEBUG = False
    CSRF_ENABLED = True
    SECRET_KEY = 'secret'
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_SALT = 'shh_this_is_a_secret'


class DevelopmentConfig(Config):
    DEBUG = True
    DB_NAME = 'ns_dev'
    DB_USER = 'postgres'
    DB_PASS = 'postgres'
    DB_SERVICE = 'postgres'
    DB_PORT = 5432
    SQLALCHEMY_DATABASE_URI = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
        DB_USER, DB_PASS, DB_SERVICE, DB_PORT, DB_NAME
    )
    PROPAGATE_EXCEPTIONS = True

class HomeConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://localhost:5433/ns_dev"
