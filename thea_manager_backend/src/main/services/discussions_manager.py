# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# General Imports
import json

from re import sub
from time import time
from uuid import uuid4
from datetime import date
from pprint import pprint
from typeguard import check_argument_types

# Logging Imports
import logging
logger = logging.getLogger(__name__)

# Boto3 Imports
from boto3 import resource
from boto3.dynamodb.conditions import Key

# Local package imports
from .workflows import Workflows
from ..models.dynamodb import Dynamo

# Utils import
from .utils import exception_handler, generate_differences_message

# ---------------------------------------------------------------
#                           Discussions Manager
# ---------------------------------------------------------------

class DiscussionsManager():

    def __init__(self) -> None:
        self._db = Dynamo()

    @exception_handler
    def create_new_discussions(self, token, object_id: str, customer_id: str, project_id: str, title: str, description: str, creator: dict):
        """
            Creates a new milestone on the milestone manager tool of Thea and stores it on DynamoDB.

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID

                title: str [required]
                    title of dicussion topic

                description: str [required]
                    description of discussion

                creator: str [required]
                    person who created discussion

            Returns:
            --------
                response: str | list
                    dict object containing project information

                http_status_code: int
                    http server status response code
        """
                
        # Type guarding
        assert check_argument_types()

        # TODO: make table name environment variable
        table_name = f"Projects-{customer_id}"

        # Key
        key = {"projectId": project_id, "customerId": customer_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        self._db.read_single_item(table_name, key, "projectId")

        # Create dynamo object
        dynamo_object = {
            "status": "open",
            "creator": creator,
            "title": title,
            "created": str(time()),
            "description": description,
            "discussionId": object_id
        }

        # DynamoDB expressions
        logger.info("Creating new discussions")
        update_expression = f"SET discussions.#discussionId = :{dynamo_object['discussionId']}"        
        expression_attribute_names = {"#discussionId": dynamo_object['discussionId']}
        expression_attribute_values = {f":{dynamo_object['discussionId']}": dynamo_object}
        self._db.update_item(table_name, key, update_expression, expression_attribute_names, expression_attribute_values)

        # Log workflow
        message = [f"Created new discussion: {title}"]
        workflow = Workflows.update_workflows(token, "Create", message, project_id, dynamo_object["discussionId"])
        self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info(f"New milestone created successfully")
        return "New discussion created successfully", 200

    @exception_handler
    def get_discussion_details(self, customer_id: str, project_id: str):
        """
            Get detailed breakdown information on a specific issue on the issue tracker tool of Thea.

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID
        

            Returns:
            --------
                response: str | list
                    dict object containing project information

                http_status_code: int
                    http server status response code
        """
       
        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query Items
        key = {"projectId": project_id, "customerId": customer_id}

        # Define project expression to get specific keys in data
        projection_expression = "discussions"

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, _ = self._db.read_single_item(table_name, key, projection_expression)
        
        if response:

            discussions = list(response["discussions"].values())

            for i, discussion in enumerate(discussions):

                response, _ = self.get_previous_messages(customer_id, discussion["discussionId"], "Discussions")

                if response:

                    discussions[i]["lastMessage"] = sorted(response, key = lambda x: x["timestamp"], reverse = False)[-1]

            return discussions, 200
        else:
            # return "Invalid issue or scope ID", 404
            return [], 404

    @exception_handler
    def update_discussion_details(self, token: str, customer_id: str, project_id: str, items: list):
        """
            Updates existing issue on the issue tracker tool of Thea and stores it on DynamoDB.

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID

                issues_id: str [required]
                    unique issue ID

                items: list [required]
                    list containing items to update on DynamoDB

            Returns:
            --------
                response: str
                    dict object containing project information

                http_status_code: int
                    http server status response code
        """

        # Type guarding
        assert check_argument_types()
        
        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"projectId": project_id, "customerId": customer_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        self._db.read_single_item(table_name, key, "projectId")

        success, fail = [], []
        for item in items:

            discussions_id = item["discussionId"]

            # Query item from DynamoDB
            projection_expression = f"discussions.{discussions_id}"
            previous_item, _ = self._db.read_single_item(table_name, key, projection_expression)
            
            if not previous_item: 
                continue
            
            previous_item = previous_item["discussions"][discussions_id]

            # Define DynamoDB expressions & update issue
            logger.info(f"Updating discussions {discussions_id}")
            item["lastUpdate"] = str(date.today())
            update_expression = "SET {}".format(", ".join(f"discussions.{discussions_id}.#{k}=:{k}" for k in item.keys()))
            expression_attribute_names = {f"#{k}": k for k in item.keys()}
            expression_attribute_values = {f":{k}": v for k, v in item.items()}
            response, http_status_code = self._db.update_item(table_name, key, update_expression, expression_attribute_names, expression_attribute_values)

            # Log workflow
            message = generate_differences_message(previous_item, item)
            if message:
                workflow = Workflows.update_workflows(token, "Update", message, project_id, discussions_id)
                self._db.create_item(f"Workflows-{customer_id}", workflow)


            if 200 <= http_status_code < 300:
                logger.info(f"Discussion {discussions_id}'s details successfully updated, {http_status_code}")
                success.append(discussions_id)
            else:
                logger.error(f"{response}, {http_status_code}")
                fail.append(discussions_id)

        # Determine status codes

        # Default vavlue
        http_status_code = 200

        if len(success)>=1 and len(fail)==0:
            http_status_code = 200
        elif len(success)==0 and len(fail)>=1:
            http_status_code = 403
        elif len(success)>=1 and len(fail)>=1:
            http_status_code = 405
        else:
            http_status_code = 304

        return {"success": success, "fail": fail}, http_status_code

    @exception_handler
    def get_previous_messages(self, customer_id: str, item_id: str, table_name: str, index_name = "itemId", last_evaluated_key: str = None):
        """
            Retrieve previous message.

            Params:

                - customer_id:
                    type: str [required]
                    descirption: unique customer ID

                - item_id:
                    type: str [required]
                    descirption: unique item ID

                - last_evaluated_key:
                    type: str [optional]
                    description: in case of pagination, last evaluate key is the starting point to the next page

            Returns:

                - response:
                    type: str | dict
                    description: dict object containing project information

                - http_status_code:
                    type: int
                    description: http server status response code
        """
       
        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"{table_name}-{customer_id}"

        key = {
            "index_val": item_id,
            "index_name": index_name
        }

        # Define project expression to get specific keys in data
        projection_expression = ", ".join([
            "customerId",
            "projectId",
            "itemId",
            "title",
            "#timestamp",
            "sender",
            "staus",
            "description",
            "messageId",
            "message"
        ])
        
        expression_attribute_names = {"#timestamp": "timestamp"}

        # Get Data
        logger.info("Querying projects overview from DynamoDB")
        return self._db.read_multiple_items(table_name, key, projection_expression, expression_attribute_names)


if __name__ == "__main__":
    dm = DiscussionsManager()