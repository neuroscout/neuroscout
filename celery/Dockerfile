FROM python:3.6-onbuild
ENV C_FORCE_ROOT true
# copy source code
COPY . /celery
WORKDIR /celery

ENTRYPOINT celery -A tasks worker --loglevel=info
