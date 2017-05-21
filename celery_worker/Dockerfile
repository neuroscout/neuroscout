FROM python:3.6-onbuild
# copy source code
COPY . /celery
WORKDIR /celery

ENTRYPOINT celery -A tasks worker --loglevel=info
