# Local package imports
import config

# Native imports
from os import getenv

# Flask imports
from flask import Flask
from flask_cors import CORS

# ---------------------------------------------------------------
#                        Create app instance
# ---------------------------------------------------------------


# Create application
def create_app():
    """
    Create Flask application

    Returns
    -------
        application
            Flask application object
    """

    # Create Flask app object
    application = Flask(__name__)
    CORS(application)

    # ---------------------------------------------------------------
    #                          Environment Configuration
    # ---------------------------------------------------------------

    # Flask env
    flask_env = getenv("FLASK_ENV", "development")

    # Configure Flask app object
    if flask_env == "development":
        application.config.from_object(config.DevConfig)

    if flask_env == "test":
        application.config.from_object(config.TestConfig)

    if flask_env == "production":
        application.config.from_object(config.ProdConfig)

    with application.app_context():

        # Import parts of our application
        from .routes.routes import api

        # Register Blueprints
        application.register_blueprint(api)

        # Return app object
        return application
