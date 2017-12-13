FROM python:3.6-onbuild
ARG DEBIAN_FRONTEND=noninteractive
RUN wget -O- http://neuro.debian.net/lists/jessie.us-nh.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xA5D32F012649A5A9
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -

RUN apt-get install -yq datalad python-nipype fsl python-opencv tesseract-ocr
RUN apt-get install -yq software-properties-common
RUN add-apt-repository ppa:joyard-nicolas/ffmpeg -y
RUN apt-get -qq update
RUN apt-get install -yq ffmpeg tesseract-ocr
RUN apt-get install -y graphviz libgraphviz-dev pkg-config

ENV FSLDIR="/usr/share/fsl/5.0"
ENV PATH="${FSLDIR}/bin:${PATH}"
RUN . /usr/share/fsl/5.0/etc/fslconf/fsl.sh

RUN apt-get install -yq nodejs
RUN npm install -g yarn

RUN pip install git+https://github.com/qmac/nipype@events-interface#egg=nipype
RUN python -c "import imageio; imageio.plugins.ffmpeg.download()"
RUN curl https://raw.githubusercontent.com/tyarkoni/pliers/master/optional-dependencies.txt | pip install -r /dev/stdin

RUN git config --global user.name "Neuroscout"
RUN git config --global  user.email "delavega@utexas.edu"

RUN crontab /usr/src/app/update.txt
RUN service cron start

WORKDIR /neuroscout
