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

    config_path = Path(__file__).resolve().parents[1] / 'config'
    FEATURE_SCHEMA = str(config_path / 'feature_schema.json')
    PREDICTOR_SCHEMA = str(config_path / 'predictor_schema.json')
    ALL_TRANSFORMERS = str(config_path / 'transformers.json')

    file_dir = Path('/file-data')

    def _init(self):
        self.DATASET_DIR = str(self.file_dir / 'datasets')
        self.FEATURE_DATASTORE = str(self.file_dir / 'feature-tracking.csv')
        self.CACHE_DIR = str(self.file_dir / 'cache')
        self.STIMULUS_DIR = str(self.file_dir / 'stimuli')
        self.EXTRACTION_DIR = str(self.file_dir / 'extracted')

class DevelopmentConfig(Config):
    ENV = 'development'
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True

class TestingConfig(Config):
    TESTING = True
    config_path = Path(__file__).resolve().parents[1] / 'tests' / 'data'
    FEATURE_SCHEMA = str(config_path / 'test_feature_schema.json')
    PREDICTOR_SCHEMA = str(config_path / 'test_predictor_schema.json')
    ALL_TRANSFORMERS = str(config_path / 'transformers.json')

class DockerTestConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/scout_test'
    FILE_DIR = Path('/tmp/file-data')

class TravisConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/travis_ci_test"
    FILE_DIR = Path('./tmp/file-data')
