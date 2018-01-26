FROM python:3.6-onbuild
ARG DEBIAN_FRONTEND=noninteractive
RUN echo "deb http://ftp.debian.org/debian jessie-backports main" | tee -a /etc/apt/sources.list
RUN apt-get -qq update
RUN apt-get install -yq ffmpeg tesseract-ocr
RUN pip install -e git+https://github.com/tyarkoni/pliers.git#egg=pliers
RUN python -c "import imageio; imageio.plugins.ffmpeg.download()"

RUN apt-get install -yq cmake libopenblas-dev liblapack-dev
RUN pip install -e git+https://github.com/davisking/dlib.git#egg=dlib
RUN curl https://raw.githubusercontent.com/tyarkoni/pliers/master/optional-dependencies.txt | pip install -r /dev/stdin

RUN wget -O- http://neuro.debian.net/lists/jessie.us-nh.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xA5D32F012649A5A9
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -

RUN apt-get install -yq datalad python-nipype python-opencv
RUN apt-get install -yq libav-tools
RUN pip install -e git+https://github.com/datalad/datalad.git#egg=datalad

RUN apt-get install -yq nodejs
RUN npm install -g yarn

RUN git config --global user.name "Neuroscout"
RUN git config --global  user.email "delavega@utexas.edu"

RUN crontab /usr/src/app/update.txt
RUN service cron start

WORKDIR /neuroscout
