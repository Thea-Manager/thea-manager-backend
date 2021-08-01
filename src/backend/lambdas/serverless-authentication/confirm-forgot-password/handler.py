# ---------------------------------------------------------------
#                            Imports
# ---------------------------------------------------------------

# Boto3 Imports
from boto3 import client

# Utils imports
from ..utils import exception_handler, compute_secret_hash

# ---------------------------------------------------------------
#                           Utils
# ---------------------------------------------------------------

# Declare boto3 cognito client
cognito = client("cognito-idp")


# Confirm password reset
@exception_handler
def confirm_forgot_password(
    client_id: str,
    client_secret: str,
    username: str,
    new_password: str,
    confirmation_code: str,
):
    """
    Account recovery method to initiate password change process

    Parameters:
    -----------

        - client_id:
            type: str [required]
            description: cognito unique client ID

        - client_secret:
            type: str [required]
            description: cognito unique client secret

        - username:
            type: str [required]
            description: username

        - new_password:
            type: str [required]
            description: new password

        - confirmation_code:
            type: str [required]
            description: password reset confirmation code

    Returns:
    --------
        - Response:
            type: None | str
            description: null if success, else error messasge

        - http_status_code:
            type: int
            description: http server status code

    Raises:
    ------

        - InternalErrorException
            Internal error

        - InvalidParameterException
            Invalid api parameters

        - InvalidPasswordException
            Password did not conform with password policy

        - LimitExceededException
            Change password requests limit exceeded

        - TooManyRequestsException
            API requests limit exceeded

        - NotAuthorizedException
            Not authorized to perform action

        - ResourceNotFoundException
            User pool or cognito app client doesn't exist

        - UserNotConfirmedException
            Cognito user not confirmed

        - UserNotFoundException
            Cognito user does not exist

        - UnexpectedLambdaException
            Unexpected exception with AWS Lambda service

        - UserLambdaValidationException
            User validation exception

        - CodeMismatchException:
            Incorrect confirmation code

        - ExpiredCodeException
            Confirmation code expired

        - TooManyFailedAttemptsException
            Too many failed attempts

        - InvalidLambdaResponseException
            Invalid lambda response
    """
    return cognito.confirm_forgot_password(
        ClientId=client_id,
        Username=username,
        Password=new_password,
        ConfirmationCode=confirmation_code,
        SecretHash=compute_secret_hash(client_id, client_secret, username),
    )


# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def handler(event, context):

    # Ingest required params
    kwargs = {
        "username": event["username"],
        "client_id": event["clientId"],
        "client_secret": event["clientSecret"],
        "new_password": event["newPassword"],
        "confirmation_code": event["confirmationCode"],
    }

    # Signin
    response, code = confirm_forgot_password(**kwargs)

    # TODO implement
    return {"body": response, "statusCode": code}
