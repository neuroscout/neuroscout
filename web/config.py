import os

class Config(object):
    DEBUG = False
    CSRF_ENABLED = True
    SECRET_KEY = 'secret'

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

class HomeConfig(Config):
	SQLALCHEMY_DATABASE_URI = "postgresql://localhost/ns_dev"
