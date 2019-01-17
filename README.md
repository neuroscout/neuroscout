# neuroscout

[![Build Status](https://travis-ci.com/PsychoinformaticsLab/neuroscout.svg?token=mytABRBRnBitJJpBpMxh&branch=master)](https://travis-ci.com/PsychoinformaticsLab/neuroscout)
[![codecov](https://codecov.io/gh/PsychoinformaticsLab/neuroscout/branch/master/graph/badge.svg)](https://codecov.io/gh/PsychoinformaticsLab/neuroscout)

To set up docker, ensure docker and docker-compose are installed.
First, set up your mounted volumes (such as /datasets), by exporting environment variables:

    DATASET_DIR=/home/myuser/datasets
    export DATASET_DIR

To set up environment variables for pliers, create a file called .pliersenv, and
configure your private keys for pliers there.

In addition, configure where file keys (such as for Google) are located:

    KEY_DIR=/home/me/.keys
    export KEY_DIR

Build the containers and start services using the development configuration:

    docker-compose build
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

The server should now be running at http://localhost/

Next, initialize, migrate and upgrade the database migrations. This script will
also add a test user.

    docker-compose exec neuroscout bash init_reset.sh


## Maintaining docker image and db

If you make a change to /neuroscout, you shoudl be able to simply restart the server.

    docker-compose restart neuroscout

If you need to upgrade the db:

    docker-compose exec neuroscout python manage.py db migrate
    docker-compose exec neuroscout python manage.py db upgrade

To inspect the database using psql:

    docker-compose run postgres psql -U postgres -h postgres

## Running tests
To run tests, after starting services, create a test database:

    docker-compose exec postgres psql -h postgres -U postgres -c "create database scout_test"

and execute:

    docker-compose run -e "APP_SETTINGS=config.app.DockerTestConfig" --rm -w /neuroscout neuroscout python -m pytest

To run frontend tests run:

    docker-compose run --rm -w /neuroscout/frontend neuroscout npm test



## Populating the database
You can use `manage.py` commands to ingest data into the database. At the least you want to add a user to be able to access the API.
[Note, for docker, precede commands with `docker-compose exec neuroscout`]

To add users:

    python manage.py add_user useremail password

To add BIDS datasets

    python manage.py add_task bids_directory_path task_name

For example for dataset ds009

    python manage.py add_task /datasets/ds009 emotionalregulation

Finally, once having added a dataset to the database, you can extract features
  using pliers into the database as follows:

    python manage.py extract_features bids_directory_path task_name graph_json

For example:

    python manage.py extract_features /datasets/ds009 emotionalregulation graph.json


Even easier, is to use a preconfigured dataset config file, such as:

    docker-compose exec neuroscout python manage.py ingest_from_json /neuroscout/config/ds009.json



## API
Once the server is up and running, you can access the API however you'd like.

The API is document using Swagger UI at:

    http://localhost/swagger-ui

### Authorization
To authorize API requests, we use JSON Web Tokens using Flask-JWT. Simply navigate to localhost:5000/auth and post the following

    {
        "username": "user@example.com",
        "password": "string"
    }

You will receive an authorization token in return, such as:

    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNDQ0OTE3NjQwLCJuYmYiOjE0NDQ5MTc2NDAsImV4cCI6MTQ0NDkxNzk0MH0.KPmI6WSjRjlpzecPvs3q_T3cJQvAgJvaQAPtk1abC_E"
    }

You can then insert this token into the header to authorize API requests:

    GET /protected HTTP/1.1
    Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eSI6MSwiaWF0IjoxNDQ0OTE3NjQwLCJuYmYiOjE0NDQ5MTc2NDAsImV4cCI6MTQ0NDkxNzk0MH0.KPmI6WSjRjlpzecPvs3q_T3cJQvAgJvaQAPtk1abC_E

Tokens expire, so you'll probably need to get a new one soon. To facilitate this, I've wrapped a Flask Client that auto authenticates and inserts the token into the header in neuroscout/tests/request_utils.py. You can use this more easily by entering into Shell mode: `python manage.py shell`. A client object will be preloaded (given the username in the file), that can be used to make requests to Flask. Make sure Flask server is also running on localhost.

Note that in order to use any protected routes, you must confirm the email on your account. Confusingly, you can get a valid token without confirming your account, but protected routes will not function until confirmation.

## Setting up front end
The frontend dependencies are managed using `yarn`

Enter the neuroscout image, and install all the necessary libraries like so:

    docker-compose exec neuroscout bash
    cd frontend
    yarn

You can then start a development server:

    yarn start

Or build a production build:

    yarn build
