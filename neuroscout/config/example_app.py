import datetime
from pathlib import Path

class Config(object):
    SERVER_NAME = 'external_host'
    ENV = 'production'
    WTF_CSRF_ENABLED = False

    SECRET_KEY = 'A_SECRET!'
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_PASSWORD_SALT = 'A_SECRET'
    JWT_EXPIRATION_DELTA = datetime.timedelta(days=7)
    JWT_AUTH_URL_RULE = '/api/auth'
    JWT_AUTH_USERNAME_KEY = 'email'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MIGRATIONS_DIR = '/migrations/migrations'

    HASH_SALT = 'dfdfdf'
    APISPEC_SWAGGER_UI_URL = None

    MAIL_SERVER = 'smtp.mailgun.com'
    MAIL_USERNAME = 'myuser'
    MAIL_PASSWORD = 'mypass'
    MAIL_DEFAULT_SENDER = 'no-reply@neuroscout.org'
    SECURITY_EMAIL_SENDER = 'no-reply@neuroscout.org'
    CONFIRM_USERS = True
    SEND_REGISTER_EMAIL = True

    CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config'
    FILE_DIR = Path('/file-data')

    CACHE_DEFAULT_TIMEOUT = 0

class DevelopmentConfig(Config):
    ENV = 'development'
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True

class TestingConfig(Config):
    TESTING = True
    CONFIG_PATH = Path(__file__).resolve().parents[1] / 'tests' / 'data'

class DockerTestConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/scout_test'
    FILE_DIR = Path('/tmp/file-data')

class TravisConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/travis_ci_test"
    FILE_DIR = Path('./tmp/file-data')
