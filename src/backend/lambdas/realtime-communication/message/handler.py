# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

import json

# ---------------------------------------------------------------
#                            Main
# ---------------------------------------------------------------


def lambda_handler(event, context):

    # TODO implement
    return {
        "statusCode": 200,
        "body": json.dumps(event["requestContext"].get("connectionId")),
    }
