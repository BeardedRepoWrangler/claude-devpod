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
    which \
    findutils \
    && dnf clean all

# Node.js v20 via NodeSource RPM
RUN curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - && \
    dnf install -y nodejs && \
    dnf clean all

# Python 3 + pip + uv
RUN dnf install -y python3 python3-pip && \
    dnf clean all && \
    pip3 install --no-cache-dir uv
