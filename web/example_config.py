class Config(object):
    DEBUG = False
    CSRF_ENABLED = True
    SECRET_KEY = 'enter key here'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "??"

class DevelopmentConfig(Config):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "??"
