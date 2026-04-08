ARG BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:9.4
FROM ${BASE_IMAGE}

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

# Podman-in-Podman dependencies
RUN dnf install -y podman fuse-overlayfs slirp4netns && \
    dnf clean all

# System-level container storage config for fuse-overlayfs
RUN mkdir -p /etc/containers && \
    printf '[storage]\ndriver = "overlay"\n\n[storage.options.overlay]\nmount_program = "/usr/bin/fuse-overlayfs"\n' \
    > /etc/containers/storage.conf

# Create non-root vscode user with sudo and Podman subuid/subgid ranges
RUN useradd -m -s /bin/bash vscode && \
    usermod -aG wheel vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode && \
    chmod 0440 /etc/sudoers.d/vscode && \
    echo "vscode:100000:65536" >> /etc/subuid && \
    echo "vscode:100000:65536" >> /etc/subgid

USER vscode
WORKDIR /home/vscode
