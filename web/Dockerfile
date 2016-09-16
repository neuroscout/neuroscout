FROM python:2.7

ADD requirements.txt /web/requirements.txt
WORKDIR /web
RUN pip install -r requirements.txt
Add . /web
CMD export APP_SETTINGS='config.DevelopmentConfig'
CMD python web/app.py