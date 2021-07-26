# Native imports
import logging
import logging.config
from os import getenv
from os.path import exists
from yaml import safe_load

# Imports
from main import create_app

# Authorship Information
__author__ = "Islam Elkadi"
__copyright__ = "Copyright 2021, Thea Manager"
__credits__ = ["Islam Elkadi"]
__license__ = "N/A"
__version__ = "1.0.0"
__maintainer__ = "Islam Elkadi"
__email__ = "islam@theamanager.com"
__status__ = "Prototype"

# ---------------------------------------------------------------
#                           Configure Logging
# ---------------------------------------------------------------

def setup_logging(default_path="log_config.yaml", default_level=logging.INFO, env_key="LOG_CFG"):
    """
        Setup logging configuration

        Parameters
        ----------

            default_path: str [required]
                file path to read logging configurations from

            default_level: required
                default logging level

            env_key: str [required]
                environment key for logging configuration
    """
    path = default_path
    value = getenv(env_key, None)

    if value:
        path = value

    if exists(path):
        with open(path, "rt") as f:
            configuration = safe_load(f.read())
        logging.config.dictConfig(configuration)
    else:
        logging.basicConfig(level=default_level)

# App object
application = create_app()

# Entry point
if __name__ == "__main__":
    setup_logging()
    application.run(host="0.0.0.0", port=5000, debug=True)
