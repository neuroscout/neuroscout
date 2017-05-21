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
    MIGRATIONS_DIR = 'migrations'
    APISPEC_SWAGGER_UI_URL = None
    HASH_SALT = 'lksjdfkljsflkjdf'
    JWT_AUTH_USERNAME_KEY = 'email'

    # Celery.
    CELERY_BROKER_URL = 'redis://:devpassword@redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://:devpassword@redis:6379/0'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_REDIS_MAX_CONNECTIONS = 5

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
