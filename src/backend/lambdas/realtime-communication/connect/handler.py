# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

import json
from os import getenv
from boto3 import resource

# ---------------------------------------------------------------
#                            Globals
# ---------------------------------------------------------------

CUSTOMER_ID = getenv("CUSTOMER_ID")

# ---------------------------------------------------------------
#                         Dynamo Utils
# ---------------------------------------------------------------

# Create dynamodb instance
db = resource("dynamodb")

# Write to dynamodb
def write(item: dict):

    # Connect to datatable
    table = db.Table(f"OnlineConnection-{CUSTOMER_ID}")

    # write to dynamo
    response = table.put_item(Item=item)

    status_code = response["ResponseMetadata"]["HTTPStatusCode"]

    if status_code == 200:
        return "Success", 200
    else:
        return "Fail", status_code


# ---------------------------------------------------------------
#                            Main
# ---------------------------------------------------------------


def handler(event, context):

    # Request body - context
    json_obj = {}
    json_obj["itemId"] = event["queryStringParameters"]["itemId"]
    json_obj["connectionId"] = event["requestContext"]["connectionId"]

    # Push to DynamoDB
    message, http_status_code = write(json_obj)

    # TODO implement
    return {
        "isBase64Encoded": False,
        "statusCode": http_status_code,
        "body": json.dumps({"message": message}),
    }
