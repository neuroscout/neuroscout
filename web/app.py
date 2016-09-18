# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
# from api import api
from database import db

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#app.register_blueprint(api, url_prefix='/api')

db.init_app(app)

from models import Dataset	

@app.route('/')
def index():
    ''' Index route '''
    return render_template('default.html')

if __name__ == '__main__':
	app.debug = True
	app.run()