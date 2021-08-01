# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from re import sub

# Boto3 Imports
from boto3 import client, resource
from botocore.exceptions import ClientError, WaiterError, ParamValidationError

# Utils imports
from ..utils import exception_handler, compute_secret_hash

# ---------------------------------------------------------------
#                  Cognito Utils
# ---------------------------------------------------------------

# Declare boto3 cognito client
cognito = client("cognito-idp")


# Intiate signin
@exception_handler
def confirm_signin(
    client_id: str,
    client_secret: str,
    username: str,
    challenge_name: str,
    session_token: str,
    mfa_code: str,
):
    """
    Authenticates users by ingesting MFA confirmation as part of the sign in process
    to verify user account

    Parameters:
    -----------

        - client_id: str [required]
            cognito unique client ID

        - client_secret: str [required]
            cognito unique client secret

        - username: str [required]
            cognito username

        - challenge_name: str [required]
            cognito challenge MFA authentication protocol

        - session_token: str [required]
            unique session token pertaining to user attempting to sign up

        - mfa_code: str [required]
            mfa code

    Returns:
    --------

        - Response:
            type: dict
            description: object containinig user access token, refresh token, and id token

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

        - TooManyRequestsException
            API requests limit exceeded

        - NotAuthorizedException
            Not authorized to perform action

        - PasswordResetRequiredException
            Password reset is required

        - ResourceNotFoundException
            User pool or cognito app client doesn't exist

        - UserNotConfirmedException
            Cognito user not confirmed

        - UserNotFoundException
            Cognito user does not exist

        - CodeMismatchException:
            Incorrect confirmation code

        - ExpiredCodeException
            Confirmation code expired

        - UnexpectedLambdaException
            Unexpected exception with AWS Lambda service

        - UserLambdaValidationException
            User validation exception

        - InvalidLambdaResponseException
            Invalid lambda response

        - InvalidUserPoolConfigurationException:
            Invalid user pool configuration

        - MFAMethodNotFoundException:
            MFA method not found

        - InvalidSmsRoleAccessPolicyException:
            Role provided for SMS configuration does not have permission to publish using Amazon SNS

        - InvalidSmsRoleTrustRelationshipException
            Invalid trust relationship with role provided with SMS configuration

        - AliasExistsException:
            Alias exists for another account

        - SoftwareTokenMFANotFoundException:
            Software TOTP MFA not enabled for user pool
    """

    if challenge_name == "SMS_MFA":
        response = cognito.respond_to_auth_challenge(
            ClientId=client_id,
            ChallengeName="SMS_MFA",
            Session=session_token,
            ChallengeResponses={
                "SMS_MFA_CODE": mfa_code,
                "USERNAME": username,
                "SECRET_HASH": compute_secret_hash(client_id, client_secret, username),
            },
        )

    if challenge_name == "SOFTWARE_TOKEN_MFA":
        response = cognito.respond_to_auth_challenge(
            ClientId=client_id,
            ChallengeName="SOFTWARE_TOKEN_MFA",
            Session=session_token,
            ChallengeResponses={
                "SOFTWARE_TOKEN_MFA_CODE": mfa_code,
                "USERNAME": username,
                "SECRET_HASH": compute_secret_hash(client_id, client_secret, username),
            },
        )

    return (
        response["AuthenticationResult"],
        response["ResponseMetadata"]["HTTPStatusCode"],
    )


@exception_handler
def get_user_details(access_token: str):
    """
    Authenticats users by ingesting MFA confirmation as part of the sign in process
    to verify user account

    Parameters:
    -----------

        - access_token: str [required]
            description: unique access token pertaining to user attempting to get user details

    Returns:
    --------

        - Response:
            type: dict
            description: object containinig user access token, refresh token, and id token

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
    return cognito.get_user(AccessToken=access_token)


# ---------------------------------------------------------------
#                           Dynamo Utils
# ---------------------------------------------------------------

# Declare boto3 dynamodb client
dynamodb = resource("dynamodb")


def create_item(table_name: str, item: dict):
    """
    Boto3 DynamoDB create operation. This enables the creation and uploading
    of a DynamoDB NoSQL object.

    Parameters:
    -----------

        - table_name:
            type: str [required]
            description: DynamoDB table name

        - item:
            type: dict [required]
            description: Dictonary based object to be pushed DynamoDB

    Returns:
    --------

        - response:
            type: str or None
            description: server response data

        - http_staus_code:
            type: int
            descrption: HTTP server response
    """

    # Target DynamoDB table
    table = dynamodb.Table(table_name)

    # Push to DynamoDB
    try:
        response = table.put_item(Item=item)
    except (ClientError, WaiterError, ParamValidationError, AttributeError) as e:
        return (
            str(e.response["Error"]["Code"]),
            e.response["ResponseMetadata"]["HTTPStatusCode"],
        )
    except Exception as e:
        return str(e), 500
    else:
        return None, response["ResponseMetadata"]["HTTPStatusCode"]


# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def handler(event, context):

    # Ingest required params
    kwargs = {
        "mfa_code": event["mfaCode"],
        "username": event["username"],
        "client_id": event["clientId"],
        "session_token": event["sessionToken"],
        "client_secret": event["clientSecret"],
        "challenge_name": event["challengeName"],
    }

    # Confirm signin
    response, code = confirm_signin(**kwargs)

    if code == 200:
        new_user_details = {}
        authenticated = True
        tokens = {
            "accessToken": response["AccessToken"],
            "refreshToken": response["RefreshToken"],
            "idToken": response["IdToken"],
        }
        for i in get_user_details(tokens["accessToken"])["UserAttributes"]:
            i = list(i.values())

            if i[0] == "name":
                new_user_details["displayName"] = i[1]
            elif i[0] == "type":
                new_user_details["userType"] = i[1]
            elif i[0] == "sub":
                new_user_details["userId"] = i[1]
            else:
                new_user_details[sub("custom:", "", i[0])] = i[1]
    else:
        new_user_details = {}
        authenticated = False
        tokens = {"accessToken": "", "refreshToken": "", "idToken": ""}

    return {
        "statusCode": code,
        "data": {"tokens": tokens, "userDetails": new_user_details},
        "authenticated": authenticated,
    }
