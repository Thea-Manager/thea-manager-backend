# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native Imports
import json
import logging

from re import sub
from time import time
from os import getenv
from uuid import uuid4
from functools import reduce

# Boto3 Imports
from boto3 import client, resource
from boto3.dynamodb.conditions import Key, And

# ---------------------------------------------------------------
#                            Globals
# ---------------------------------------------------------------

CUSTOMER_ID=getenv("CUSTOMER_ID")
WEBSOCKET_ENDPOINT=getenv("WEBSOCKET_ENDPOINT")

# ---------------------------------------------------------------
#                           Configs
# ---------------------------------------------------------------

db = resource("dynamodb")
websock_client = client("apigatewaymanagementapi", endpoint_url = WEBSOCKET_ENDPOINT)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                           DynamoDB
# ---------------------------------------------------------------

# Write to dynamodb
def write(item: dict):

    # Connect to datatable
    table = db.Table(f"Discussions-{CUSTOMER_ID}")
    
    # write to dynamo
    response = table.put_item(Item = item)
    
    status_code = response['ResponseMetadata']['HTTPStatusCode']
    
    if status_code == 200:
        return "Success", 200
    else:
        return "Fail", status_code

# Retrieve
def read_multiple_items(table_name: str, projection_expression: str, filters: dict, last_evaluated_key: dict = None, limit = 1000):
    """
        Boto3 DynamoDB read operation. This enables the querying and reading
        of multiple DynamoDB NoSQL object.

        Params:

            - table_name: 
                type: str [required]
                description: DynamoDB table name

            - key:
                type: dict [required]
                description: Dictonary based object containing the filters to query DynamoDB

            - projection_expression: 
                type: str [required]
                description: filter expression indicating keys to query from database. If none, then all keys of object are returned

            - last_evaluated_key:
                type: str [optional]
                description: used during pagination, is the key of the last item evaluated and to continue from instead of querynig
                             the whole object

            - limit:
                type: int [optional]
                description: how many keys to return durnig query

        Returns:

            - response:
                type: str or list
                description: server response data

            - http_staus_code:
                type: int
                descrption: HTTP server response
    """
   
    # Target DynamoDB table
    response = db.Table(table_name).scan(
        ProjectionExpression = projection_expression,
        FilterExpression=reduce(And, ([Key(k).eq(v) for k, v in filters.items()]))
    )

    if "Items" in response.keys():
        logger.info(f"{response['Items']} - response['ResponseMetadata']['HTTPStatusCode']")
        return response["Items"], response['ResponseMetadata']['HTTPStatusCode']
    else:
        logger.error(f"Empty results - {response['ResponseMetadata']['HTTPStatusCode']}")
        return None, response['ResponseMetadata']['HTTPStatusCode']

# ---------------------------------------------------------------
#                           Main
# ---------------------------------------------------------------


def lambda_handler(event, context):
    
    # Request body - get message body
    request_body = json.loads(event["body"])["message"]
    
    # Query data table, get list of tokens matching project ID
    connection_ids, _ = read_multiple_items(f"OnlineConnection-{CUSTOMER_ID}", "connectionId", {"itemId": request_body["projectId"]})
    
    # Establish unix timestamp
    timestamp = str(time())
    
    # Add timestamp to request body
    request_body["timestamp"] = timestamp
    
    # Send message to websocket channel
    for token in connection_ids:
        websock_client.post_to_connection(
            ConnectionId = token["connectionId"], 
            Data = json.dumps(request_body)
        )
        
    # Write to db
    item = {
        "messageId": sub("-", "", str(uuid4())),
        "timestamp": request_body["timestamp"],
        "customerId": request_body["customerId"],
        "projectId": request_body["projectId"],
        "message": request_body["message"],
        "sender": request_body["sender"],
        "itemId": request_body["itemId"]
    }
    write(item)
    
    # TODO implement
    return {
        'statusCode': 200,
        "body": json.dumps(request_body)
    }