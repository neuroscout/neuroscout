#! /bin/bash
rm -r /migrations/migrations
python manage.py db init
python manage.py db migrate
python manage.py db upgrade

python manage.py add_user test2@test.com password
