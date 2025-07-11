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
    # Install libpcap-dev for packet capture functionality
RUN apt-get install -y libpcap-dev

# Copy the dependency file to leverage Docker cache
COPY ./deploy/inventor-requirements.txt .

# Upgrade pip and install project dependencies
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r inventor-requirements.txt

# Install YAML module for PowerShell
RUN pwsh -Command 'Set-PSRepository -Name "PSGallery" -InstallationPolicy Trusted; Install-Module -Name powershell-yaml -Scope CurrentUser -Force' 

# Copy the rest of the application code
COPY . .

# Define the default command to run your application
CMD ["pwsh"]
