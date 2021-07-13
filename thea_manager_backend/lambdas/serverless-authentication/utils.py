# ---------------------------------------------------------------
#                            Imports
# ---------------------------------------------------------------

# Native imports
import logging
from re import sub

# Security imports
from hmac import new
from hashlib import sha256
from base64 import b64encode

# ---------------------------------------------------------------
#                            Globals
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                            Utils
# ---------------------------------------------------------------


def exception_handler(func):
    def inner_function(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except Exception as e:
            if type(e).__name__ == "InternalErrorException":
                logger.error("InternalErrorException - Internal error")
                return "Internal error", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "CodeMismatchException":
                logger.error("CodeMismatchException - Incorrect confirmation code")
                return "Incorrect confirmation code", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "LimitExceededException":
                logger.error("LimitExceededException - Too many signin attempts, try after sometime")
                return "Too many signin attempts, try after sometime", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "InvalidPasswordException":
                logger.error("InvalidPasswordException - Password did not conform with policy")
                return "Password did not conform with policy", e.response['ResponseMetadata']['HTTPStatusCode']      
            elif type(e).__name__ == "NotAuthorizedException":
                logger.error(f"NotAuthorizedException - {e.args[0]}")
                return sub(r"[1-9]*[a-zA-Z]+[1-9]+", "", e.args[0]), e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "ResourceNotFoundException":
                logger.error("ResourceNotFoundException - Invalid client ID, user pool client doesn't exist")
                return "Invalid client ID, user pool client doesn't exist", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "InvalidParameterException":
                logger.error(f"InvalidParameterException - {e.args[0]}")
                return sub(r"[1-9]*[a-zA-Z]+[1-9]+", "", e.args[0]), e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "UsernameExistsException":
                logger.error("UsernameExistsException - Email ID already exists")
                return "Email ID already exists", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "ExpiredCodeException":
                logger.error("ExpiredCodeException - Confirmation code expired")
                return "Confirmation code expired", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "TooManyRequestsException":
                logger.error("TooManyRequestsException - Too many requests")
                return "Too many requests", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "UserNotFoundException":
                logger.error("UserNotFoundException - User does not exist")
                return "User does not exist", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "UserNotConfirmedException":
                logger.error("UserNotConfirmedException - User not confirmed")
                return "User not confirmed", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "UnexpectedLambdaException":
                logger.error("UnexpectedLambdaException - Unexpected exception with AWS Lambda service")
                return "Unexpected exception with AWS Lambda service", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "UserLambdaValidationException":
                logger.error("UserLambdaValidationException - User validation exception")
                return "User validation exception", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "TooManyFailedAttemptsException":
                logger.error("TooManyFailedAttemptsException - Too many failed attempts")
                return "Too many failed attempts", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "InvalidLambdaResponseException":
                logger.error("InvalidLambdaResponseException - Invalid lambda response")
                return "Invalid lambda response", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "InvalidUserPoolConfigurationException":
                logger.error("InvalidUserPoolConfigurationException - Invalid user pool configuration")
                return "Invalid user pool configuration", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "MFAMethodNotFoundException":
                logger.error("MFAMethodNotFoundException - MFA method not found")
                return "MFA method not found", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "AliasExistsException":
                logger.error("AliasExistsException - Alias exists for another account")
                return "Alias exists for another account", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "PasswordResetRequiredException":
                logger.error("PasswordResetRequiredException - Password reset requried")
                return "Password reset requried", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "SoftwareTokenMFANotFoundException":
                logger.error("SoftwareTokenMFANotFoundException - Software TOTP MFA not enabled for user pool")
                return "Software TOTP MFA not enabled for user pool", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "InvalidSmsRoleTrustRelationshipException":
                logger.error("InvalidSmsRoleTrustRelationshipException - Invalid trust relationship with role provided with SMS configuration")
                return "Invalid trust relationship with role provided with SMS configuration", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "InvalidSmsRoleAccessPolicyException":
                logger.error("InvalidSmsRoleAccessPolicyException - Role provided for SMS configuration does not have permission to publish using Amazon SNS")
                return "Role provided for SMS configuration does not have permission to publish using Amazon SNS", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "InvalidEmailRoleAccessPolicyException":
                logger.error("InvalidEmailRoleAccessPolicyException - Amazon Cognito is not allowed to use your email identity")
                return "Amazon Cognito is not allowed to use your email identity", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "CodeDeliveryFailureException":
                logger.error("CodeDeliveryFailureException - Verification code failes to delivery successfully")
                return "Verification code failed to be successfully delivered", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "ConcurrentModificationException":
                logger.error("ConcurrentModificationException - multiple modification happening concurrently")
                return "Concurrent modifications occuring", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "EnableSoftwareTokenMFAException":
                logger.error("EnableSoftwareTokenMFAException - code mismatch and service fails to configure the software token TOTP multi-factor authentication (MFA)")
                return "MFA code mismatch", e.response['ResponseMetadata']['HTTPStatusCode']
            else:
                return str(e), 500
        else:
            return None, response['ResponseMetadata']['HTTPStatusCode']
    return inner_function


# Comput secret hash
def compute_secret_hash(client_id: str, client_secret: str, username: str):
    """
        Computes the secret hash for AWS Cognito APIs that require it. This secret has is a
        keyed-hash message authentication code (HMAC) calculated using the secret key of a 
        user pool client and username plus the client ID in the message.

       Parameters:
       -----------

            - client_secret:
                type: str [required]
                description: client secret provided by cognito

            - client_id:
                type: str [required]
                description: The ID of the client associated with the user pool

            - username:
                type: str [required]
                description: The user name of the user you wish to register/authenticate

        returns:

            - computed_hash:
                type: str [required]
                description: HMAC SHA256 computed hash
    """
    message = username + client_id
    dig = new(client_secret.encode('UTF-8'), msg=message.encode('UTF-8'), digestmod=sha256).digest()
    return b64encode(dig).decode()