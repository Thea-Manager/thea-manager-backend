# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
import logging
from re import sub

# Boto3 Imports
from boto3 import client, resource

# Utils Imports
from ..utils import exception_handler

# ---------------------------------------------------------------
#                  Cognito Utils
# ---------------------------------------------------------------

# Declare boto3 cognito client
cognito = client("cognito-idp")

# Get user details          
@exception_handler
def get_user_details_cognito(access_token: str):
    """
        Authenticates users by ingesting MFA confirmation as part of the sign in process 
        to verify user account

        Parameters:
        -----------

            - access_token: str [required]
                unique access token pertaining to user attempting to get user details
                         
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

            - InvalidParameterException
                Invalid api parameters

            - ResourceNotFoundException
                User pool or cognito app client doesn't exist

            - UserNotConfirmedException
                Cognito user not confirmed

            - UserNotFoundException
                Cognito user does not exist

            - InternalErrorException
                Internal error

            - NotAuthorizedException
                Not authorized to perform action

            - TooManyRequestsException
                API requests limit exceeded

            - PasswordResetRequiredException
                Password reset is required
    """
    return cognito.get_user(AccessToken = access_token)

# ---------------------------------------------------------------
#                           DynamoDB Utils
# ---------------------------------------------------------------

# Declare dynamodb client
dynamodb = resource("dynamodb")

# Retrieve
def read_single_item(table_name: str, key: dict, projection_expression: str, expression_attribute_names: dict = None, expression_attribute_values: dict = None):
    """
        Read single item from Dynamo table.

        Parameters
        ----------

            table_name: str [required]
                DynamoDB table name to be queried

            key: dict [required]
                Dictonary based object containing the filters to query DynamoDB

            projection_expression: str [required]
                Filter expression indicating keys to query from database. If none, then all keys of object are returned

        Returns
        -------

            response: str | list
                server response data

            http_staus_code: int
                HTTP server response

        Raises
        ------

            ClientError
                Boto3 client service related error when making API request

            ParamValidationError
                Error is raised when incorrect parameters provided to boto3
                API method
    """
 
    # Target DynamoDB table
    table = dynamodb.Table(table_name)

    # kwargs
    kwargs = {
        "Key": key,
        "ProjectionExpression": projection_expression,
        "ExpressionAttributeNames": expression_attribute_names,
        "ExpressionAttributeValues": expression_attribute_values,
        "ConsistentRead": True    
    }

    kwargs = {k:v for k,v in kwargs.items() if v}

    return table.get_item(**kwargs).get("Item"), 200

def get_user_details_dynamo(email: str, organization_id: str):
    """
        Get additional user details from DynamoDB

        Parameters:
        -----------

            - email: str [required]
                user email ID

            - organization_id: str [required]
                organization ID

        Returns:
        --------

            - user_details: dict
                user details object

            - https_status_code: int
                https server response code
    """

    # Query key
    key = {"email": email}

    # Projection expression
    projection_expression = ", ".join([
        "userId",
        "orgId",
        "#name",
        "email",
        "username",
        "userType"
    ])
    
    expression_attribute_names = {"#name":"name"}

    # Return server response
    return read_single_item(f"users-{organization_id}", key, projection_expression, expression_attribute_names)

# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------

def handler(event, context):
    
    # Confirm signin
    response = get_user_details_cognito(event["accessToken"])

    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:

        # Format user attributes response
        user_attributes_1 = {sub("custom:", "", x["Name"]): x["Value"] for x in response["UserAttributes"]}
        
        user_attributes_2, code = get_user_details_dynamo(user_attributes_1["email"], user_attributes_1["orgId"])
        
        # merge response objects
        response = {**user_attributes_1, **user_attributes_2}
    
        auth_valid = True
        
        code = 200        
    else:
        code = 500
        response = {}
        auth_valid = False
    
    return {
        'data': response,
        'statusCode': code,
        "authValid": auth_valid
    }
    