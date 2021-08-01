# ---------------------------------------------------------------
#                            Imports
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


@exception_handler
def resend_signup_confirmation_code(client_id: str, client_secret: str, username: str):
    """
    Resends the user a confirmaion code to their email to verify ownership

    Parameters:
    -----------

        - client_id: str [required]
            description: The ID of the client associated with the user pool

        - client_secret: str [required]
            description: client secret provided by cognito

        - username: str [required]
            description: The user name of the user you wish to register/authenticate

    Returns:
    --------

        - response: None | str
            description: null if success, error messaage if fail

        - http_staus_code: int
            descrption: HTTP server response

    Raises:
    ------

        - InternalErrorException
            Internal error

        - InvalidParameterException
            Invalid parameter for cognito

        - TooManyRequestsException
            API requests limit exceeded

        - NotAuthorizedException
            Not authorized to perform action

        - ResourceNotFoundException
            User pool or cognito app client doesn't exist

        - UserNotFoundException
            Cognito user does not exist

        - UnexpectedLambdaException
            Unexpected exception with AWS Lambda service

        - UserLambdaValidationException
            User validation exception

        - InvalidLambdaResponseException
            Invalid lambda response

        - InvalidSmsRoleAccessPolicyException:
            Role provided for SMS configuration does not have permission to publish using Amazon SNS

        - InvalidSmsRoleTrustRelationshipException
            Invalid trust relationship with role provided with SMS configuration

        - LimitExceededException
            Change password requests limit exceeded

        - CodeDeliveryFailureException
            Thrown when a verification code fails to deliver successfully

        - InvalidEmailRoleAccessPolicyException
            Cognito doesn't have permission to use email identity
    """
    response = cognito.resend_confirmation_code(
        ClientId=client_id,
        Username=username,
        SecretHash=compute_secret_hash(client_id, client_secret, username),
    )
    return None, response["ResponseMetadata"]["HTTPStatusCode"]


# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def lambda_handler(event, context):

    # Ingest requried params
    kwargs = {
        "username": event["username"],
        "client_id": event["clientId"],
        "client_secret": event["clientSecret"],
    }

    # Sign up
    response, code = resend_signup_confirmation_code(**kwargs)

    # TODO implement
    return {"statusCode": code, "body": response}
