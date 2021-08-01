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


# Intiate password reset
@exception_handler
def forgot_password(client_id: str, client_secret: str, username: str):
    """
    Account recovery method to initiate password change process

    Parameters:
    -----------

        - client_id: str [required]
            description: cognito unique client ID

        - client_secret: str [required]
            description: cognito unique client secret

        - username: str [required]
            description: username

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

        - InvalidParameterException
            Invalid api parameters

        - LimitExceededException
            Change password requests limit exceeded

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

        - InvalidLambdaResponseException
            Invalid lambda response

        - InternalErrorException
            Internal error

        - InvalidPasswordException
            Password did not conform with password policy

        - InvalidSmsRoleAccessPolicyException:
            Role provided for SMS configuration does not have permission to publish using Amazon SNS

        - InvalidSmsRoleTrustRelationshipException
            Invalid trust relationship with role provided with SMS configuration

        - InvalidEmailRoleAccessPolicyException
            Cognito doesn't have permission to use email identity

        - CodeDeliveryFailureException
            Thrown when a verification code fails to deliver successfully
    """
    return cognito.forgot_password(
        ClientId=client_id,
        Username=username,
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
    }

    # Signin
    response, code = forgot_password(**kwargs)

    # TODO implement
    return {"body": response, "statusCode": code}
