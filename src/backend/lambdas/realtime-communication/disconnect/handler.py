# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

import json
from os import getenv
from boto3 import client

# ---------------------------------------------------------------
#                            Globals
# ---------------------------------------------------------------

CUSTOMER_ID = getenv("CUSTOMER_ID")

# ---------------------------------------------------------------
#                            Dynamo Utils
# ---------------------------------------------------------------

# Create dynamodb instance
db = client("dynamodb")

# Write to dynamodb


def delete(item: dict):

    # write to dynamo
    response = db.delete_item(
        TableName=f"OnlineConnection-{CUSTOMER_ID}", Key=item)

    status_code = response["ResponseMetadata"]["HTTPStatusCode"]

    if status_code == 200:
        return "Success", 200
    else:
        return "Fail", status_code


# ---------------------------------------------------------------
#                            Main
# ---------------------------------------------------------------


def lambda_handler(event, context):

    # Request body
    json_obj = {"connectionId": {"S": event["requestContext"]["connectionId"]}}

    # Push to DynamoDB
    message, http_status_code = delete(json_obj)

    # TODO implement
    return {
        "isBase64Encoded": False,
        "statusCode": http_status_code,
        "body": json.dumps({"message": message}),
    }
