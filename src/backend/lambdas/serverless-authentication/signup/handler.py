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
def signup(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
    user_attributes: dict,
):
    """
    Signs up user via AWS cognito. By default, when a user signs up, that user is not
    verified and will be required to verify ownership of their account. Verification
    details are ALWAYS sent to the user's email.

    Parameters:
    ------------

        - client_secret:
            type: str [required]
            description: client secret provided by cognito

        - client_id:
            type: str [required]
            description: The ID of the client associated with the user pool

        - username:
            type: str [required]
            description: The user name of the user you wish to register/authenticate

        - password:
            type: str [required]
            description: user's password

    Returns:
    --------

        - response:
            type: None | str
            description: null if success, error messaage if fail

        - http_status_code:
            type: int
            descrption: HTTP server response

    Raises:
    -------

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

        - CodeDeliveryFailureException
            Thrown when a verification code fails to deliver successfully

        - InvalidEmailRoleAccessPolicyException
            Cognito doesn't have permission to use email identity

        - InvalidPasswordException
            Password did not conform with password policy

        - UsernameExistsException
            Username already exists
    """
    return cognito.sign_up(
        ClientId=client_id,
        Username=username,
        Password=password,
        SecretHash=compute_secret_hash(client_id, client_secret, username),
        UserAttributes=[{"Name": k, "Value": v} for k, v in user_attributes.items()],
    )


# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def handler(event, context):

    # Ingest requried params
    kwargs = {
        "username": event["username"],
        "password": event["password"],
        "client_id": event["clientId"],
        "client_secret": event["clientSecret"],
        "user_attributes": event["userAttributes"],
    }

    # Sign up
    response, code = signup(**kwargs)

    if code == 200:
        response = {
            "UserConfirmed": response["UserConfirmed"],
            "CodeDeliveryDetails": response["CodeDeliveryDetails"],
        }

    # Response body
    return {"data": response, "statusCode": code}
