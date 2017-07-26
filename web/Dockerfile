FROM python:3.6-onbuild
ARG DEBIAN_FRONTEND=noninteractive
RUN wget -O- http://neuro.debian.net/lists/jessie.us-nh.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xA5D32F012649A5A9
RUN apt-get update
RUN apt-get install -yq datalad
