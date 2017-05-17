import datetime

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'secret'
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_SALT = 'shh_this_is_a_secret'
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_DELTA = datetime.timedelta(days=7)
    JWT_AUTH_URL_RULE = '/api/auth'
    MIGRATIONS_DIR = 'migrations'
    APISPEC_SWAGGER_UI_URL = None
    HASH_SALT = 'lksjdfkljsflkjdf'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
    MIGRATIONS_DIR = '/migrations/migrations'

class DockerTestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/scout_test'
    TESTING = True

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/scout_test'
    TESTING = True

class TravisConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/travis_ci_test"
    TESTING = True

class HomeConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
    DEBUG = True
