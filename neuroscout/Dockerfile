FROM python:3.6-stretch
ARG DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apt-get -qq update
RUN apt-get install -yq ffmpeg tesseract-ocr
RUN pip install -e git+https://github.com/tyarkoni/pliers.git#egg=pliers
RUN pip install clarifai duecredit google-api-python-client IndicoIo librosa>=0.6.3 pysrt pytesseract spacy rev_ai
RUN python -m pliers.support.download
RUN apt-get install apt-transport-https

RUN wget -O- http://neuro.debian.net/lists/stretch.us-nh.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net 0xA5D32F012649A5A9
RUN apt-get update
RUN apt-get install -yq datalad
RUN pip install datalad

RUN curl -sSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN echo "deb https://deb.nodesource.com/node_11.x jessie main" | tee /etc/apt/sources.list.d/nodesource.list
RUN echo "deb-src https://deb.nodesource.com/node_11.x jessie main" | tee -a /etc/apt/sources.list.d/nodesource.list
RUN apt-get update
RUN apt-get install -y nodejs
RUN npm install -g yarn

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

RUN git config --global user.name "Neuroscout"
RUN git config --global  user.email "delavega@utexas.edu"

RUN python -m pliers.support.setup_yamnet

RUN crontab /usr/src/app/update.txt
RUN service cron start

WORKDIR /neuroscout
