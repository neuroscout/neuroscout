""" Set up app database """
from flask_sqlalchemy import SQLAlchemy
from models.base import Base

db = SQLAlchemy(model_class=Base)
