FROM ubuntu:20.04 

LABEL mainteiner="Tadeo"

ENV LOCATION smart
ENV PREFERRED_PROTOCOL auto
ENV LIGHTWAY_CIPHER auto

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl \
    && rm -rf /tmp/*.deb

RUN apt-get --allow-releaseinfo-change update \
    && apt install -y net-tools \
    && apt-get install -y --no-install-recommends \
    ca-certificates figlet expect iproute2 nano make gnupg procps libnm0 

RUN apt-get update && apt-get install -y python3 python3-dev python3-pip

RUN echo "Instalando librerias Python" \
    && python3 -m pip install --no-cache-dir --upgrade pip setuptools \
    && pip install pyvirtualdisplay playwright \
    && python3 -m playwright install \
    && python3 -m playwright install-deps

USER root
