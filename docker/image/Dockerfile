FROM continuumio/anaconda:latest

RUN apt-get update
# install gcc
RUN apt-get install gcc -y

# create base environment tcb
ADD environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml

