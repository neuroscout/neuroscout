#! /bin/bash
cd ~/repos/neuroscout/web
psql -c 'drop database neuroscout'
rm -r migrations

psql -c 'create database neuroscout'
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
