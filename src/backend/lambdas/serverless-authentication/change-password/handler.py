# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Boto3 Imports
from boto3 import client

# Utils Imports
from ..utils import exception_handler

# ---------------------------------------------------------------
#                           Cognito Utils
# ---------------------------------------------------------------

# Declare boto3 cognito client
cognito = client("cognito-idp")

# Change password
@exception_handler
def change_passsword(old_pass: str, new_pass: str, access_token: str):
    """
        API route to change cognito user's password.

        Parameters
        ----------

            - old_pass: str [required]
                original password

            - new_pass: str [required]
                new password

            - access_token: str [required]
                access token JWT

        Returns
        -------

            response: str
                success message

            status_code: int
                https response code

        Raises
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

            - PasswordResetRequiredException
                Password reset is required

            - ResourceNotFoundException
                User pool or cognito app client doesn't exist

            - UserNotConfirmedException
                Cognito user not confirmed

            - UserNotFoundException
                Cognito user does not exist
    """
    cognito.change_password(
        PreviousPassword = old_pass,
        ProposedPassword = new_pass,
        AccessToken = access_token)
    
    return "Password changed", 200

# ---------------------------------------------------------------
#                           Utils
# ---------------------------------------------------------------

def handler(event, context):
    
    # Request body
    kwargs = {
        "old_pass": event["oldPassword"],
        "new_pass": event["newPassword"],
        "access_token": event["accessToken"],
    }
    
    # Change password
    response, code = change_passsword(**kwargs)
    
    # TODO implement
    return {
        "data": response,
        "statusCode": code
    }
