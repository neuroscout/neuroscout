from database import db
from flask import current_app

class Dataset(db.Model):
	id = db.Column(db.Integer, primary_key=True)	

class Predictors(db.Model):
	pass

class Users(db.Model):
	pass

class Extractors(db.Model):
	pass

class Apps(db.Model):
	pass

class Results(db.Model):
	pass