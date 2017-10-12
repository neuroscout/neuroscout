import datetime

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'secret'
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_PASSWORD_SALT = 'shh_this_is_a_secret'
    WTF_CSRF_ENABLED = False
    JWT_EXPIRATION_DELTA = datetime.timedelta(days=7)
    JWT_AUTH_URL_RULE = '/api/auth'
    JWT_AUTH_USERNAME_KEY = 'email'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HASH_SALT = 'lksjdfkljsflkjdf'
    MIGRATIONS_DIR = 'migrations'
    APISPEC_SWAGGER_UI_URL = None

    MAIL_SERVER = 'smtp.mailgun.org'
    MAIL_USERNAME = 'postmaster@sandbox313ed2a0563245c1827937801e1676a8.mailgun.org'
    MAIL_PASSWORD = 'YhhgT$y30LzD'
    MAIL_DEFAULT_SENDER = 'no-reply@neuroscout.org'
    SECURITY_EMAIL_SENDER = 'no-reply@neuroscout.org'

    CONFIRM_USERS = True
    SEND_REGISTER_EMAIL = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
    MIGRATIONS_DIR = '/migrations/migrations'
    DATASET_DIR = '/file-data'

class DockerTestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres@postgres:5432/scout_test'
    TESTING = True

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/scout_test'
    TESTING = True
    DATASET_DIR = '/tmp/file-data'

class TravisConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/travis_ci_test"
    TESTING = True
    DATASET_DIR = '/tmp/file-data'

class HomeConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://zorro:dbpass@localhost:5432/neuroscout'
    PROPAGATE_EXCEPTIONS = True
    DEBUG = True
