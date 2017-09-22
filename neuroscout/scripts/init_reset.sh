#! /bin/bash
rm -r /migrations/migrations
rm -r migrations
python manage.py db init
python manage.py db migrate
python manage.py db upgrade

python manage.py add_user user@example.com string
