""" This is an EXAMPLE config file
 Rename this file to app.py and set variables
"""

import datetime
from pathlib import Path


class Config(object):
    # SERVER_NAME = localhost
    GOOGLE_CLIENT_ID = 'clientid'  # Must set this for frontend to build
    SECRET_KEY = 'A_SECRET!'
    HASH_SALT = 'dfdfdf'
    SECONDARY_HASH_SALT = 'something_else'
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_PASSWORD_SALT = 'A_SECRET'

    MAIL_SERVER = 'smtp.mailgun.com'
    MAIL_USERNAME = 'myuser'
    MAIL_PASSWORD = 'mypass'
    MAIL_DEFAULT_SENDER = 'no-reply@neuroscout.org'
    SECURITY_EMAIL_SENDER = 'no-reply@neuroscout.org'

    # The rest of the variables variables are good defaults -- can leave as is
    CONFIRM_USERS = True
    SEND_REGISTER_EMAIL = True

    JWT_EXPIRATION_DELTA = datetime.timedelta(days=7)
    JWT_AUTH_URL_RULE = '/api/auth'
    JWT_AUTH_USERNAME_KEY = 'email'

    # Core variables
    CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config'
    FILE_DIR = Path('/file-data')
    MIGRATIONS_DIR = '/migrations/migrations'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_DEFAULT_TIMEOUT = 0
    APISPEC_SWAGGER_UI_URL = None
    WTF_CSRF_ENABLED = False
    ENV = 'production'
    NEUROVAULT_ACCESS_TOKEN = 'something'

    SQLALCHEMY_DATABASE_URI = 'postgres://postgres:password@postgres:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True


class ProductionConfig(Config):
    SENTRY_URI = ''


class DevelopmentConfig(Config):
    SERVER_NAME = 'localhost'
    ENV = 'development'


class TestingConfig(Config):
    TESTING = True
    CONFIG_PATH = Path(__file__).resolve().parents[1] / 'tests' / 'data'


class DockerTestConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/scout_test'
    FILE_DIR = Path('/tmp/file-data')


class GHIConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:password@localhost/ci_test"
    FILE_DIR = Path('./tmp/file-data').absolute()


class GHIConfigBackend(GHIConfig):
    SERVER_NAME = 'localhost'
