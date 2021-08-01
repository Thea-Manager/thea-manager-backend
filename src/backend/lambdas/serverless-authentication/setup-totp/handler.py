# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Boto3 Imports
from boto3 import client

# Utils Imports
from ..utils import exception_handler, compute_secret_hash

# ---------------------------------------------------------------
#                           Utils
# ---------------------------------------------------------------

# Declare boto3 cognito client
cognito = client("cognito-idp")

# Intiate signin
@exception_handler
def setup_totp(session_token: str, secret_code: str = "", mfa_code: str = ""):
    """
    Sets up or verifies TOTP MFA for new user. If secret code & mfa code are
    not provided, it is assumed that this is a first time user whose TOTP MFA
    is being configured for the first time.


    Parameters:
    -----------

        - session_token: str [required]
            unique session token pertaining to unique user

        - secret_code: str [optional]
            secret code returned to setup MFA

        - mfa_code: str [optional]
            TOTP MFA Code

    Returns:
    --------

        - session_token:
            type: str [required]
            description: unique session token pertaining to unique user

        - secret_code:
            type: str
            description: secret code returned to setup MFA

        - status:
            type: str
            description: TOTP MFA setup status

        - http_status_code:
            type: str
            description: server response code

    Raises:
    -------

        - InternalErrorException
            Internal error

        - CodeMismatchException:
            Incorrect confirmation code

        - SoftwareTokenMFANotFoundException:
            Software TOTP MFA not enabled for user pool

        - NotAuthorizedException
            Not authorized to perform action

        - InvalidParameterException
            Invalid api parameters

        - UserNotFoundException
            Cognito user does not exist

        - UserNotConfirmedException
            Cognito user not confirmed

        - ResourceNotFoundException
            User pool or cognito app client doesn't exist

        - TooManyRequestsException
            API requests limit exceeded

        - PasswordResetRequiredException
            Password reset is required

        - InvalidUserPoolConfigurationException:
            Invalid user pool configuration

        - SoftwareTokenMFANotFoundException:
            Software TOTP MFA not enabled for user pool

        - ConcurrentModificationException
            Exception is thrown if two or more modifications are happening concurrently.

        - EnableSoftwareTokenMFAException:
            Code mismatch and service fails to configure the software token TOTP multi-factor authentication (MFA)
    """
    if session_token and not secret_code and not mfa_code:
        response = cognito.associate_software_token(Session=session_token)
        return {
            "sessionToken": response["Session"],
            "secretCode": response["SecretCode"],
        }, response["ResponseMetadata"]["HTTPStatusCode"]

    if session_token and secret_code and mfa_code:
        response = cognito.verify_software_token(
            AccessToken=secret_code, Session=session_token, UserCode=mfa_code
        )

    return {
        "status": response["Status"],
        "sessionToken": response["Session"],
        "response": response,
    }, response["ResponseMetadata"]["HTTPStatusCode"]


# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def handler(event, context):

    # Ingest required params
    kwargs = {
        "mfa_code": event["mfaCode"],
        "secret_code": event["secretCode"],
        "session_token": event["sessionToken"],
    }

    # Signin
    response, code = setup_totp(**kwargs)

    # TODO implement
    return {"data": response, "statusCode": code}
