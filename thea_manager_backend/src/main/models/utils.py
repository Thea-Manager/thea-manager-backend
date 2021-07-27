# Native imports
from functools import wraps

# Logging imports
import logging
logger = logging.getLogger(__name__)

# Boto3 imports
from botocore.exceptions import ClientError, ParamValidationError, WaiterError

# ---------------------------------------------------------------
#                           Decorator Methods
# ---------------------------------------------------------------

def exception_handler(func):
    """
        Global exception handling decorator to catch Boto3 related errors

        Parameters
        ----------
            func: <method>
                Method to be wrapped and executed within this decorater

        Returns
        -------
            inner_function:
                Output of executed wrapped method
    """
    # @wraps(func)
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ClientError, ParamValidationError, WaiterError, AttributeError) as e:
            logger.error(f"Code: {e.response['Error']['Code']} - Message: {e.response['Error']['Message']} - HttpStatus: {e.response['ResponseMetadata']['HTTPStatusCode']}")
            raise
    return inner_function
