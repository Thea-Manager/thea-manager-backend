#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Logging Imports
import logging
logger = logging.getLogger(__name__)

# General Imports
from typeguard import check_argument_types

# Utils Imports
from .utils import exception_handler

# Local package imports
from ..models.dynamodb import Dynamo

# ---------------------------------------------------------------
#                       User Manager
# ---------------------------------------------------------------

class UserManager():
    """
        Class to programatically manage users on the Thea manager app

        Attributes
        ----------
            _db:
                DynamoDB object instance

        Methods
        -------
            get_unique_user(organization_id, user_id)

            get_user_overview(organization_id, last_evaluated_key)
    """

    def __init__(self) -> None:
        self._db = Dynamo()

    @exception_handler
    def get_unique_user(self, organization_id: str, email: str):
        """
            Get unique user's details

            Parameters:
            -----------
                organization_id: str [required]
                    unique organization ID user belongs to

                email: str [required]
                    unique user ID

            Returns:
            --------
                response: list | str
                    unique user details
        """

        # Type guarding
        assert check_argument_types()

        # Query key
        key = {"email": email, "orgId": organization_id}

        # Projection expression
        projection_expression = ", ".join([
            "userId",
            "orgId",
            "name",
            "email",
            "username",
            "userType"
        ])

        # Query DynamoDB request
        logger.info(f"Checking if user ID or organization ID exists: {key}")

        # Return server response
        return  self._db.read_single_item("users", key, projection_expression)

    @exception_handler
    def get_user_overview(self, organization_id: str, last_evaluated_key: str = None):
        """
            Get overview of users

            Parameters:
            -----------
                organization_id: str [required]
                    unique organization ID user belongs to

                last_evaluated_key: str [optional]
                    in case of pagination, last evaluate key is the starting point to the next page

            Returns:
            --------
                response: str | dict
                    dict object containing project information

                http_status_code: int
                    http server status response code           
        """

        # Type guarding
        assert check_argument_types()

        key = {
            "index_name": "orgId",
            "index_val": organization_id
        }

        # Define project expression to get specific keys in data
        projection_expression = ", ".join([
            "userId",
            "email",
            "userType",
            "username",
            "#name",
            "orgId"
        ])

        expression_attribute_names = {"#name":"name"}

        # Get Data
        logger.info("Querying users overview from DynamoDB")
        return self._db.read_multiple_items(f"users-{organization_id}", key, projection_expression, expression_attribute_names)

if __name__ == "__main__":
    user_manager = UserManager()