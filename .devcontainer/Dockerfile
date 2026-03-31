FROM registry.access.redhat.com/ubi9/ubi:latest

# System packages
RUN dnf install -y --allowerasing \
    git \
    curl \
    wget \
    jq \
    vim \
    nano \
    tar \
    unzip \
    shadow-utils \
    sudo \
    procps-ng \
    && dnf clean all
