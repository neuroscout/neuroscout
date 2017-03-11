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


class DevelopmentConfig(Config):
    DEBUG = True
    DB_NAME = 'neuroscout'
    DB_USER = 'postgres'
    DB_PASS = ''
    DB_SERVICE = 'postgres'
    DB_PORT = 5432
    SQLALCHEMY_DATABASE_URI = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
        DB_USER, DB_PASS, DB_SERVICE, DB_PORT, DB_NAME
    )
    PROPAGATE_EXCEPTIONS = True

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://localhost:5433/scout_test"
    TESTING = True

class TravisConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/travis_ci_test"
    TESTING = True

class HomeConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
