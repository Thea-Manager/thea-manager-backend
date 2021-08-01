# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from re import sub
from uuid import uuid4

# Boto3 Imports
from boto3 import client, resource
from botocore.exceptions import ClientError, WaiterError, ParamValidationError

# Utils imports
from ..utils import exception_handler, compute_secret_hash

# ---------------------------------------------------------------
#                            Cognito Utils
# ---------------------------------------------------------------

# Declare boto3 cognito client
cognito = client("cognito-idp")


# Confirm signup
@exception_handler
def confirm_signup(
    client_id: str, client_secret: str, username: str, confirmation_code: str
):
    """
    Confirm a new user's signup. This takes in a confiration code that was sent to the user upon
    signing up to the platform. Also note, that a user cannot create a profile if username or email
    exists.

    Parameters:
    ------------

        - client_id:
            type: str [required]
            description: The ID of the client associated with the user pool

        - client_secret:
            type: str [required]
            description: client secret provided by cognito

        - username:
            type: str [required]
            description: The user name of the user you wish to register/authenticate

        - confirmation_code:
            type: str [required]
            description: confirmation code to verify signup

    Returns:
    --------

        - response:
            type: None | str
            description: null if success, error messaage if fail

        - http_staus_code:
            type: int
            descrption: HTTP server response
    """
    return cognito.confirm_sign_up(
        ClientId=client_id,
        Username=username,
        SecretHash=compute_secret_hash(client_id, client_secret, username),
        ConfirmationCode=confirmation_code,
    )


# ---------------------------------------------------------------
#                           Dynamo Utils
# ---------------------------------------------------------------

# Declare boto3 dynamodb client
dynamodb = resource("dynamodb")


# Write data to dynamodb table
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

    Raises:
    -------

        - ClientError

        - WaiterError

        - ParamValidationError

        - AttributeError
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


# Store user details on dynamo
def store_user_details(table_name: str, user_details: dict):
    """
    Stores user details on DynamoDB

    Parameters:
    -----------

        - table_name: str [required]
            name of data table

        - user_details: dict [required]
            user detail object

    Returns:
    --------

        - response:
            dynamodb server response

        - http_status_code: int
            http server code response
    """
    user_details["userId"] = sub("-", "", str(uuid4()))

    # remove custom: prefix
    dynamo_object = {sub("custom:", "", key): val for key, val in user_details.items()}

    # Push to dynamodb
    response, http_status_code = create_item(table_name, dynamo_object)

    return response, http_status_code


# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def handler(event, context):

    # Ingest requried params
    username = event["username"]
    client_id = event["clientId"]
    client_secret = event["clientSecret"]
    user_attributes = event["userAttributes"]
    confirmation_code = event["confirmationCode"]

    # Sign up
    response, code = confirm_signup(
        client_id, client_secret, username, confirmation_code
    )

    if code == 200:

        # Store user details to Dynamodb
        response, code = store_user_details(
            f"users-{user_attributes['custom:orgId']}", user_attributes
        )

    # TODO implement
    return {"data": response, "statusCode": code}
