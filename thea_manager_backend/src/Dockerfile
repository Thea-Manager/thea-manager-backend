# Pull verified base python image from dockerhub
FROM python:3.8

# Declare container maintainer & version
LABEL maintainer = "Islam Elkadi - islam@theamanger.com"

# Upgrade pip as ROOT
RUN pip install --upgrade pip

# # Add non-root user
# RUN useradd -m -s /bin/false thea-worker
# USER thea-worker

# Make app directory working directory
WORKDIR /home/app

# Copy repo files into container
COPY . /home/app

# # Change ownership to added user
# COPY --chown=thea-worker:thea-worker . .

# Install application dependencies
RUN pip install --user -r /home/app/requirements.txt

EXPOSE 5000

# Application entry point to start flask server
ENTRYPOINT ["python3","/home/app/application.py"]
