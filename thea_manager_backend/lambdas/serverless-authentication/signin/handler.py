# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Security imports
from hmac import new
from hashlib import sha256
from base64 import b64encode

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
def signin(auth_flow: str, username: str, password: str, client_id: str, client_secret: str):
    """
        Enbales user to sign in.

        Parameters:
        ------------

            - auth_flow:
                type: str [required]
                description: type of authentication flow method

            - client_id:
                type: str [required]
                description: cognito unique client ID

            - client_secret:
                type: str [required]
                description: cognito unique client secret

            - username:
                type: str [required]
                description: username

            - password:
                type: str [required]
                description: password

        Returns:
        --------

            - response:
                type: str
                description: returns challenge name and session token for unique user

            - https_status_code:
                type: str
                description: server http status code

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

            - UserNotConfirmedException
                Cognito user not confirmed

            - PasswordResetRequiredException
                Password reset is required

            - InvalidUserPoolConfigurationException:
                Invalid user pool configuration
    """
    response = cognito.initiate_auth(
        ClientId = client_id,
        AuthFlow = auth_flow,
        AuthParameters = {
            'USERNAME': username,
            'PASSWORD': password,
            'SECRET_HASH': compute_secret_hash(client_id, client_secret, username)
        })
    return {"challengeName": response["ChallengeName"], "sessionToken": response["Session"]}, response["ResponseMetadata"]["HTTPStatusCode"]
 
# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def handler(event, context):
    
    # Ingest required params
    kwargs = {
        "username": event["username"],
        "password": event["password"],
        "auth_flow": event["authFlow"],
        "client_id": event["clientId"],
        "client_secret": event["clientSecret"]
    }
    
    # Signin
    response, code = signin(**kwargs)
    
    # TODO implement
    return {
        'data': response,
        'statusCode': code
    }