FROM python:3.6-onbuild
ARG DEBIAN_FRONTEND=noninteractive
ADD ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
WORKDIR /celery_worker
