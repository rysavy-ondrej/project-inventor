# Use an official Python runtime as a base image
# This is Debian Bookworm Linux
FROM python:3.9.21-bookworm AS python-ref


# Prevent Python from writing .pyc files to disk and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /inventor

# Install system dependencies (if needed, e.g., gcc for compiling packages)
RUN apt-get update 
    # Install pre-requisite packages.
RUN apt-get install -y wget 
    # Download the Microsoft repository GPG keys
RUN wget -q https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb 
    # Register the Microsoft repository GPG keys
RUN dpkg -i packages-microsoft-prod.deb 
    # Delete the Microsoft repository GPG keys file
RUN rm packages-microsoft-prod.deb 
    # Update the list of packages after we added packages.microsoft.com
RUN apt-get update 
    ###################################
    # Install PowerShell
RUN apt-get install -y powershell 
RUN rm -rf /var/lib/apt/lists/*
    # Install runtime system libraries / tools:
    #  - libpcap0.8: the runtime libpcap shared library. scapy loads it via
    #    ctypes to compile the BPF capture filter used by the security.tls
    #    monitor's sniffer; without it scapy raises
    #    "Cannot set filter: libpcap is not available. Cannot compile filter !".
    #    Only the runtime lib is needed here, not the libpcap-dev headers.
    #  - kcat (kafkacat): required by the Out-Kafka.ps1 result sink to publish
    #    monitoring results to a Kafka topic.
RUN apt-get update && apt-get install -y libpcap0.8 kcat && rm -rf /var/lib/apt/lists/*

# Copy the dependency file to leverage Docker cache
COPY ./deploy/inventor-requirements.txt .

# Upgrade pip and install project dependencies
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r inventor-requirements.txt


# Install YAML module for PowerShell
RUN pwsh -Command 'Set-PSRepository -Name "PSGallery" -InstallationPolicy Trusted; Install-Module -Name powershell-yaml -Scope CurrentUser -Force' 

# Copy the rest of the application code
COPY . .

# Default: idle forever -- so we can exec inside to test and troubleshoot the container
CMD ["tail", "-f", "/dev/null"]
