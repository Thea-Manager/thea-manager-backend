# Imports
from os import getenv, path
from dotenv import load_dotenv

# Define base directory
base_dir = path.abspath(path.dirname(__file__))

# Load env variables
if path.exists(path.join(base_dir, ".env")):
    load_dotenv(path.join(base_dir, ".env"))
else:
    load_dotenv()

# Dev configurations
class DevConfig:
    DEBUG = True
    TESTING = True
    # FLASK_RUN_PORT = 5000
    # FLASK_RUN_HOST = "0.0.0.0"
    REGION = getenv("REGION")
    FLASK_ENV = "development"
    SECRET_KEY = getenv("SECRET_KEY")
    SESSION_COOKIE_NAME = getenv("SESSION_COOKIE_NAME")


# Test configurations
class TestConfig:
    DEBUG = False
    TESTING = True
    FLASK_ENV = "test"
    REGION = getenv("REGION")
    # FLASK_RUN_PORT = 6000
    # FLASK_RUN_HOST = "0.0.0.0"
    SECRET_KEY = getenv("SECRET_KEY")
    SESSION_COOKIE_NAME = getenv("SESSION_COOKIE_NAME")


# Prod configurations
class ProdConfig:
    DEBUG = False
    TESTING = False
    REGION = getenv("REGION")
    FLASK_ENV = "production"
    # FLASK_RUN_PORT = 7000
    # FLASK_RUN_HOST = "0.0.0.0"
    SECRET_KEY = getenv("SECRET_KEY")
    SESSION_COOKIE_NAME = getenv("SESSION_COOKIE_NAME")
