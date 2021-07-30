#!/usr/bin/env python

# ---------------------------------------------------------------
#                              Imports
# ---------------------------------------------------------------

# Native Imports
from re import sub
from time import time
from uuid import uuid4
from typeguard import check_argument_types

# Logging Imports
import logging
logger = logging.getLogger(__name__)

# Utils Imports
from .utils import get_token_claims

# Local package imports
from ..models.dynamodb import Dynamo

# ---------------------------------------------------------------
#                          Workflows Manager
# ---------------------------------------------------------------

class Workflows():
    """
        Class to programatically manage a project's workflows

        Attributes
        ----------
            _db:
                DynamoDB object instance

        Methods
        -------
            update_workflows(jwt, action, message, project_id, scope_id, item_id)
                Updates a project's workflows

            get_workflows(customer_id: str, project_id: str, type_id: str, actions)
                Retrieves a project's workflows and filters them based on item ID
    """

    def __init__(self) -> None:
        self._db = Dynamo()

    @staticmethod
    def update_workflows(jwt: str, action: str, message: list, project_id: str, item_id: str):
        """
            Updates a project's workflow and stores in on DynamoDB

            Parameters:
            -----------
                jwt: str [required]
                    User ID JSON Web Token containing user infoormationo in payload
            
                action: str [required]
                    action tag to label workflow type (options: create, update, add, remove, delete)

                message: list [required]
                    list of messaegs to append to workflow item

                project_id: str [required]
                    unique project ID

                scope_id: str [required]
                    unique project ID

                item_id: str [required]
                    item's UUID to filter objects


             Returns:
             --------
                dynamo_object: dict
                    dynamo_object to add to database
        """
        # Type guarding
        assert check_argument_types()

        # Validate JWT
        decoded_jwt = get_token_claims(jwt)

        # Create workflow object
        dynamo_object = {
            "itemId": sub("-", "", str(uuid4())),
            "meta": message,
            "action": action,
            "typeId": item_id,
            "projectId": project_id,
            "email": decoded_jwt["email"],
            "name": decoded_jwt["name"],
            "username": decoded_jwt["custom:username"],
            "timestamp": str(time()),
        }

        return dynamo_object

    def get_workflows(self, customer_id: str, project_id: str, type_id: str, actions: list):
        """
            Retrieves a project's workflow data from DynamoDB

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer id

                project_id: str [required]
                    unique project ID

                type_id: str [required]
                    UUID project ID

                item_id: str [required]
                    item's UUID to filter objects

                actions: list [required]
                    list of workflow actions to filter and retrieve

             Returns:
             --------
                workflows: list
                    list of workflow items and associated details

                http_status_code: int
                    http server response status code
        """
        # Type guarding
        assert check_argument_types()
        
        # Query Items
        key = {"projectId": project_id, "customerId": customer_id}

        # TODO: Make table name an config env variable
        table_name = f"Workflows-{customer_id}"

        key = {
            "index_name": "typeId",
            "index_val": type_id
        }

        # Define project expression to get specific keys in data
        projection_expression = ",".join([
            "itemId",
            "#action",
            "#name",
            "meta",
            "#timestamp",
            "projectId",
            "typeId",
            "email",
            "userName"
        ])

        expression_attribute_names = {"#action": "action", "#timestamp": "timestamp", "#name":"name"}

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        workflows, http_status_code = self._db.read_multiple_items(table_name, key, projection_expression, expression_attribute_names)

        if actions:
            workflows = [x for x in workflows if x["action"] in actions]

        if type_id:
            workflows = [x for x in workflows if x["typeId"]==type_id]

        workflows = sorted(workflows, key = lambda i: i['timestamp'])
        
        return workflows, http_status_code