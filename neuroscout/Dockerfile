FROM python:3.8-bullseye
ARG DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /usr/src/app/neuroscout
WORKDIR /usr/src/app/neuroscout

RUN apt-get -qq update
RUN apt-get install -yq ffmpeg tesseract-ocr apt-transport-https libnss3 xvfb
RUN pip install pliers clarifai duecredit google-api-python-client librosa>=0.6.3 pysrt pytesseract spacy rev_ai

RUN wget -O- http://neuro.debian.net/lists/bullseye.us-tn.libre | tee /etc/apt/sources.list.d/neurodebian.sources.list 
RUN apt-key adv --recv-keys --keyserver hkps://keyserver.ubuntu.com 0xA5D32F012649A5A9
RUN apt-get update
RUN apt-get install -yq datalad-container

RUN curl -sSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN echo "deb https://deb.nodesource.com/node_12.x buster main" | tee /etc/apt/sources.list.d/nodesource.list
RUN echo "deb-src https://deb.nodesource.com/node_12.x buster main" | tee -a /etc/apt/sources.list.d/nodesource.list
RUN apt-get update
RUN apt-get install -y nodejs
RUN npm install -g yarn

COPY requirements.txt /usr/src/app/neuroscout/
COPY optional_requirements.txt /usr/src/app/neuroscout/
RUN pip install setuptools==45
RUN pip uninstall -y enum34
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r optional_requirements.txt
RUN python -m pliers.support.download
RUN python -m pliers.support.setup_yamnet

COPY . /usr/src/app/neuroscout

RUN git config --global user.name "Neuroscout"
RUN git config --global  user.email "delavega@utexas.edu"

RUN crontab /usr/src/app/neuroscout/update.txt
RUN service cron start

WORKDIR /usr/src/app/neuroscout/frontend

RUN cp /usr/src/app/neuroscout/frontend/src/config.ts.prod /usr/src/app/neuroscout/frontend/src/config.ts
RUN yarn install && yarn build

WORKDIR /usr/src/app/
