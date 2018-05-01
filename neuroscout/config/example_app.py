import datetime
from pathlib import Path

class Config(object):
    SERVER_NAME = 'external_host'
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'A_SECRET!'
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_PASSWORD_SALT = 'A_SECRET'
    WTF_CSRF_ENABLED = False
    JWT_EXPIRATION_DELTA = datetime.timedelta(days=7)
    JWT_AUTH_URL_RULE = '/api/auth'
    JWT_AUTH_USERNAME_KEY = 'email'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HASH_SALT = 'dfdfdf'
    MIGRATIONS_DIR = 'A_SECRET'
    APISPEC_SWAGGER_UI_URL = None

    MAIL_SERVER = 'smtp.mailgun.com'
    MAIL_USERNAME = 'myuser'
    MAIL_PASSWORD = 'mypass'
    MAIL_DEFAULT_SENDER = 'no-reply@neuroscout.org'
    SECURITY_EMAIL_SENDER = 'no-reply@neuroscout.org'

    CONFIRM_USERS = True
    SEND_REGISTER_EMAIL = True

    dir_path = Path(__file__).resolve().parents[1]
    FEATURE_SCHEMA = (dir_path / 'config/feature_schema.json').as_posix()
    ALL_TRANSFORMERS = (dir_path / 'config/transformers.json').as_posix()

    STIMULUS_DIR = 'path'
    EXTRACTION_DIR = 'path'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
    MIGRATIONS_DIR = '/migrations/migrations'
    DATASET_DIR = '/file-data/datasets'
    FEATURE_DATASTORE = '/file-data/feature-tracking.csv'

class TestingConfig(Config):
    TESTING = True
    dir_path = Path(__file__).resolve().parents[1]
    FEATURE_SCHEMA = (dir_path / 'tests/data/test_feature_schema.json').as_posix()
    FEATURE_DATASTORE = '/tmp/file-data/feature-tracking.csv'

class DockerTestConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/scout_test'
    DATASET_DIR = '/tmp/file-data'

class HomeTestingConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/scout_test'

class TravisConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/travis_ci_test"
    DATASET_DIR = './tmp/file-data'
    FEATURE_DATASTORE = './tmp/datastore.csv'
    STIMULUS_DIR = './tmp/stims'
    EXTRACTED_DIR = './tmp/extracted'

class HomeConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
    DEBUG = True
