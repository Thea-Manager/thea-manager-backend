#####################################################
#                    Build stage                    #
#####################################################

# Pull verified base python image from dockerhub
FROM python:3.9-alpine3.14 as build

# Create app directory & make it current workdir
COPY . /app
WORKDIR /app

# Install dependencies
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

#####################################################
#                  Release stage                    #
#####################################################

# Pull Python3 distroless image
FROM python:3.9-alpine3.14 as release

# Add non-root user
RUN adduser -D -s /bin/false thea-worker
USER thea-worker

# Copy built packages to current environment
COPY --from=build /app /app
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Make /app workdir and set env path
WORKDIR /app
ENV PYTHONPATH=/usr/local/lib/python3.9/site-packages

# Change ownership to added user
COPY --chown=thea-worker:thea-worker . .

# Expose app port
EXPOSE 5000

# Application entry point to start flask server
ENTRYPOINT ["python3","/app/application.py"]
