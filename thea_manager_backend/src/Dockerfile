# Pull verified base python image from dockerhub
FROM python:3.8-slim-buster

# Declare container maintainer & version
LABEL maintainer = "Islam Elkadi - islam@theamanger.com"
LABEL version = "1.0.0"

# Upgrade pip as ROOT
RUN pip install --upgrade pip

# Make app directory working directory
COPY . /home/app
WORKDIR /home/app

# Install application dependencies
RUN pip install --user -r /home/app/requirements.txt

# Application entry point to start flask server
ENTRYPOINT ["python3","/home/app/app.py"]