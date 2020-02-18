FROM python:3.6-stretch
ARG DEBIAN_FRONTEND=noninteractive
ADD ./celery_worker/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
ADD ./ /neuroscout
RUN pip install /neuroscout
WORKDIR /celery_worker
