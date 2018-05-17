FROM python:3.6-onbuild
ARG DEBIAN_FRONTEND=noninteractive
RUN pip install -r /neuroscout/neuroscout/requirements.txt
RUN pip install -e /neuroscout
WORKDIR /celery_worker
