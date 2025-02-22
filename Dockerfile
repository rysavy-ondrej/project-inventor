# Use an official Python runtime as a base image
FROM python:3.10-slim

# Prevent Python from writing .pyc files to disk and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (if needed, e.g., gcc for compiling packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy the dependency file to leverage Docker cache
COPY ./deploy/inventor-requirements.txt .

# Upgrade pip and install project dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r inventor-requirements.txt

# Copy the rest of the application code
COPY . .

# Define the default command to run your application
CMD ["python", "app.py"]
