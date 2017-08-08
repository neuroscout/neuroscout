FROM python:3.6-onbuild
ARG DEBIAN_FRONTEND=noninteractive
RUN wget -O- http://neuro.debian.net/lists/jessie.us-nh.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xA5D32F012649A5A9
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g yarn
RUN apt-get install -yq datalad
RUN apt-get install -yq python-nipype
RUN cd frontend; yarn build
RUN pip install git+https://github.com/qmac/nipype --user
