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
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/scout_test'
    TESTING = True

class TravisConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/travis_ci_test"
    TESTING = True

class HomeConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
