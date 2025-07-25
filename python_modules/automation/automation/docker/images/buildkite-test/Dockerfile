####################################################################################################
#
# DAGSTER BUILDKITE TEST
#
# This Dockerfile specifies an image that serves as base for all Python testing
# steps (both integration and unit) run on BK.
#
####################################################################################################
ARG BASE_IMAGE
FROM "${BASE_IMAGE}" AS system_base

LABEL maintainer="Dagster Labs"

# Never prompts the user for choices on installation/configuration of packages (NOTE:
# DEBIAN_FRONTEND does not affect the apt-get command)
ENV DEBIAN_FRONTEND=noninteractive \
    TERM=linux

# Set correct locale first and install deps for installing debian packages
RUN apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
    apt-transport-https \
    curl \
    ca-certificates \
    gnupg2 \
    locales \
    lsb-release \
    # Set locale
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8

# Envionment variables that will be referenced during installation of various packages
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    DOCKER_COMPOSE_VERSION=1.29.1 \
    KIND_VERSION=v0.14.0 \
    KUBECTL_VERSION=v1.20.1 \
    FOSSA_VERSION=1.1.10

# Install Kubernetes tools: kubectl, kind, helm
RUN curl -LO "https://storage.googleapis.com/kubernetes-release/release/$KUBECTL_VERSION/bin/linux/amd64/kubectl" \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl \
    && curl -L "https://github.com/kubernetes-sigs/kind/releases/download/$KIND_VERSION/kind-linux-amd64" -o ./kind \
    && chmod +x ./kind \
    && mv ./kind /usr/local/bin/kind \
    && curl "https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3" | bash

# Install libxmlsec to use xmlsec
RUN apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
    libxmlsec1-dev \
    pkg-config

# Install Java (required by pyspark) - Java 17 for compatibility with both Spark 3 and 4
COPY --from=openjdk:17-slim-buster /usr/local/openjdk-17 /usr/local/openjdk-17
ENV JAVA_HOME /usr/local/openjdk-17
RUN update-alternatives --install /usr/bin/java java /usr/local/openjdk-17/bin/java 1

# Install various packages used in running/installing/testing Dagster:
# - git/make (cloning dagster, running checks defined in Makefile)
# - nodejs/yarn (dagster UI)
# - assorted others-- some may no longer be required, but leaving in place for now
#
# deb.nodesource script adds node source to apt
RUN curl -sL https://deb.nodesource.com/setup_21.x | bash - \
    # Add yarn GPG key and apt source
    && curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | \
    gpg --dearmor -o /usr/share/keyrings/yarnkey.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/yarnkey.gpg] https://dl.yarnpkg.com/debian/ stable main" | \
    tee -a /etc/apt/sources.list.d/yarn.list >/dev/null \
    # Deal with slim variants not having man page directories (which causes "update-alternatives" to fail)
    && mkdir -p /usr/share/man/man1 /usr/share/man/man2 \
    && apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
    build-essential \
    bzip2 \
    cron \
    g++ \
    gcc \
    git \
    make \
    mariadb-client \
    nodejs \
    pandoc \
    postgresql \
    rabbitmq-server \
    rsync \
    ssh \
    software-properties-common \
    unzip \
    wget \
    xz-utils \
    yarn

# Install FOSSA cli for analyzing our open-source dependencies
# https://github.com/fossas/fossa-cli
RUN wget https://github.com/fossas/fossa-cli/releases/download/v${FOSSA_VERSION}/fossa-cli_${FOSSA_VERSION}_linux_amd64.tar.gz \
    && tar xvzf fossa-cli_${FOSSA_VERSION}_linux_amd64.tar.gz fossa \
    && chmod +x ./fossa \
    && mv ./fossa /usr/local/bin/fossa \
    && rm fossa-cli_${FOSSA_VERSION}_linux_amd64.tar.gz \
    && fossa --version

# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install#deb
# Add Google Cloud GPG key and apt source
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null \
    && apt-get -yqq update \
    && apt-get -yqq install \
    google-cloud-cli

# Install Docker -- note that we have some older code using `docker-compose` instead of `docker
# compose`, so we have to install both the `docker-compose` executable and the docker compose CLI
# plugin. Eventually we should update the code using `docker-compose` and then we can just use the
# CLI plugin.
# See: https://docs.docker.com/engine/install/debian/
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | \
    gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | \
    tee -a /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get -yqq update \
    && apt-get -yqq install \
    docker-ce docker-ce-cli containerd.io docker-compose-plugin \
    # Install docker-compose
    && curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /bin/

# Install redis
RUN wget http://download.redis.io/redis-stable.tar.gz \
    && tar xvzf redis-stable.tar.gz \
    && cd redis-stable \
    && make install

# Install the DuckDB CLI
RUN curl --fail --silent --show-error --location \
    --output duckdb_cli-linux-amd64.zip \
    https://github.com/duckdb/duckdb/releases/download/v1.1.3/duckdb_cli-linux-amd64.zip \
    && unzip duckdb_cli-linux-amd64.zip \
    && mv duckdb /usr/local/bin/duckdb \
    && chmod +x /usr/local/bin/duckdb

# Clean up
RUN apt-get remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean

# Temp image used to get non-dagster Python dependencies
FROM system_base AS snapshot_builder

# Build a requirements file with all non-Dagster packages that are dependencies of a Dagster
# package. We also install `awscli` (used in Buildkite) at this stage so that it can be installed
# together with Dagster dependencies. This allows pip's dependency resolver to account for
# everything.
RUN git clone --depth 1 https://github.com/dagster-io/dagster.git

WORKDIR dagster

ENV VIRTUAL_ENV=/usr/local
ENV UV_HTTP_TIMEOUT=300
RUN python scripts/install_dev_python_modules.py --system awscli || exit 1
RUN uv pip freeze --exclude-editable > /snapshot-reqs.txt

# Final image includes both system deps and preinstalled non-Dagster python deps
FROM system_base

COPY --from=snapshot_builder /snapshot-reqs.txt .

# Preinstall non-Dagster packages in image so that the virtual environment
# builds faster in Buildkite.
RUN uv pip install --system -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt

# New versions of debian require allowlisting folders where `git` can run
RUN git config --system --add safe.directory \*
