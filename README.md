# neuroscout

[![Build Status](https://travis-ci.com/PsychoinformaticsLab/neuroscout.svg?token=mytABRBRnBitJJpBpMxh&branch=master)](https://travis-ci.com/PsychoinformaticsLab/neuroscout)

To set up docker, ensure docker and docker-compose are installed.
Next, edit docker-compose.yml to configure mounting of data volumes.

Build the containers and start the services:

    docker-compose build
    docker-compose up -d

The server should now be running at http://localhost:80/

Next, initialize, migrate and upgrade the database migrations. This script will
also add a test user.

    docker-compose exec web bash init_reset.sh


## Maintaining docker image and db

If you make a change to /web but don't want your db to be nuked, reload like this:

    docker-compose up -d --no-deps --build web

If you need to upgrade the db:

    docker-compose exec web python manage.py db migrate
    docker-compose exec web python manage.py db upgrade

To inspect the database using psql:

    psql -h localhost -p 5432 -U postgres --password

If you want to reset the database to an empty state then rebuild and restart
all services:

    docker-compose down

and run the original initialization commands above.

## Running tests
To run tests, after starting services, create a test database:

    docker-compose exec postgres psql -h postgres -U postgres -c "create database scout_test"

and execute:

    docker-compose run -w /web web python -m pytest

To run frontend tests run:

docker-compose run -w /web/frontend web npm test



## Populating the database
You can use `manage.py` commands to ingest data into the database. At the least you want to add a user to be able to access the API.
[Note, for docker, precede commands with `docker-compose exec web`]

To add users:

    python manage.py add_user useremail password

To add BIDS datasets

    python manage.py add_dataset bids_directory_path task_name

For example for dataset ds009

    python manage.py add_dataset /datasets/ds009 emotionalregulation

Finally, once having added a dataset to the database, you can extract features
  using pliers into the database as follows:

    python manage.py extract_features bids_directory_path task_name graph_json

For example:

    python manage.py extract_features /datsets/ds009 emotionalregulation graph.json


## API
Once the server is up and running, you can access the API however you'd like.

The API is document using Swagger UI at:

    http://localhost:5000/

### Authorization
To authorize API requests, we use JSON Web Tokens using Flask-JWT. Simply navigate to localhost:5000/auth and post the following

    {
        "username": "joe",
        "password": "pass"
    }

You will receive an authorization token in return, such as:

    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNDQ0OTE3NjQwLCJuYmYiOjE0NDQ5MTc2NDAsImV4cCI6MTQ0NDkxNzk0MH0.KPmI6WSjRjlpzecPvs3q_T3cJQvAgJvaQAPtk1abC_E"
    }

You can then insert this token into the header to authorize API requests:

    GET /protected HTTP/1.1
    Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNDQ0OTE3NjQwLCJuYmYiOjE0NDQ5MTc2NDAsImV4cCI6MTQ0NDkxNzk0MH0.KPmI6WSjRjlpzecPvs3q_T3cJQvAgJvaQAPtk1abC_E

Tokens expire, so you'll probably need to get a new one soon. To facitate this, I've wrapped a Flask Client that auto authenticates and inserts the token into the header in web/tests/request_utils.py. You can use this more easily by entering into Shell mode: `python manage.py shell`. A client object will be preloaded (given the username in the file), that can be used to make requests to Flask. Make sure Flask server is also running on localhost.
