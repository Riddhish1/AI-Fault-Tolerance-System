FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    stress-ng \
    wget \
    gnupg2 \
    lsb-release \
    curl \
    supervisor \
    tar \
    rsync \
    iproute2 \
    procps \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Install Telegraf
RUN wget -q https://dl.influxdata.com/telegraf/releases/telegraf_1.21.4-1_amd64.deb && \
    dpkg -i telegraf_1.21.4-1_amd64.deb && \
    rm telegraf_1.21.4-1_amd64.deb

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Create app directory
WORKDIR /app

# Copy shared scripts
COPY shared/ /app/shared/

# Set Python path
ENV PYTHONPATH=/app

CMD ["/bin/bash"] 