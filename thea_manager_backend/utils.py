#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import getenv
from dotenv import load_dotenv

# CDK Imports - Core
from aws_cdk.core import (
    RemovalPolicy
)

# CDK Imports - DynamoDB
from aws_cdk.aws_dynamodb import (
    Attribute,
    AttributeType,
    BillingMode,
    TableEncryption,
    ProjectionType
)

# ---------------------------------------------------------------
#                        Env variables
# ---------------------------------------------------------------

# Load env vars
load_dotenv()
ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# ---------------------------------------------------------------
#                          Configurations
# ---------------------------------------------------------------


######################################
#       DynamoDB Configurations      #
######################################

dynamodb_configurations={
    "projects":{
        "table_configuration": {
            "id":f"Projects-{ACCOUNT_NUMBER}",
            "table_name":f"Projects-{ACCOUNT_NUMBER}",
            "partition_key":Attribute(
                name="projectId",
                type=AttributeType.STRING
            ),
            "billing_mode":BillingMode.PAY_PER_REQUEST,
            "encryption":TableEncryption.AWS_MANAGED,
            "removal_policy":RemovalPolicy.DESTROY
            # "read_capacity":5, # enabled if billing mode is PROVISIONED
            # "write_capacity":5, # enabled if billing mode is PROVISIONED
            # "replication_regions":[],
        },
        "global_secondary_index": [
            {
                "partition_key":Attribute(
                    name="customerId",
                    type=AttributeType.STRING
                ),
                # "read_capacity":5, # enabled if Table's billing mode is PROVISIONED
                # "write_capacity":5, # enabled if Table's billing mode is PROVISIONED
                "index_name":"customerId",
                "projection_type":ProjectionType.ALL # Default
            }
        ]
    },
    "workflows":{
        "table_configuration": {
            "id":f"Workflows-{ACCOUNT_NUMBER}",
            "table_name":f"Workflows-{ACCOUNT_NUMBER}",
            "partition_key":Attribute(
                name="itemId",
                type=AttributeType.STRING
            ),
            "billing_mode":BillingMode.PAY_PER_REQUEST,
            "encryption":TableEncryption.AWS_MANAGED,
            "removal_policy":RemovalPolicy.DESTROY
            # "read_capacity":5, # enabled if billing mode is PROVISIONED
            # "write_capacity":5, # enabled if billing mode is PROVISIONED
            # "replication_regions":[],
        },
        "global_secondary_index": [
            {
                "partition_key":Attribute(
                    name="typeId",
                    type=AttributeType.STRING
                ),
                # "read_capacity":5, # enabled if Table's billing mode is PROVISIONED
                # "write_capacity":5, # enabled if Table's billing mode is PROVISIONED
                "index_name":"typeId",
                "projection_type":ProjectionType.ALL # Default
            }
        ]
    },
    "chat_records":{
        "table_configuration": {
            "id":f"ChatRecords-{ACCOUNT_NUMBER}",
            "table_name":f"ChatRecords-{ACCOUNT_NUMBER}",
            "partition_key":Attribute(
                name="messageId",
                type=AttributeType.STRING
            ),
            "billing_mode":BillingMode.PAY_PER_REQUEST,
            "encryption":TableEncryption.AWS_MANAGED,
            "removal_policy":RemovalPolicy.DESTROY
            # "read_capacity":5, # enabled if billing mode is PROVISIONED
            # "write_capacity":5, # enabled if billing mode is PROVISIONED
            # "replication_regions":[],
        },
        "global_secondary_index": [
            {
                "partition_key":Attribute(
                    name="itemId",
                    type=AttributeType.STRING
                ),
                # "read_capacity":5, # enabled if Table's billing mode is PROVISIONED
                # "write_capacity":5, # enabled if Table's billing mode is PROVISIONED
                "index_name":"itemId",
                "projection_type":ProjectionType.ALL # Default
            }
        ]
    },
    "connections_manager_":{
        "table_configuration": {
            "id":f"OnlineConnection-{ACCOUNT_NUMBER}",
            "table_name":f"OnlineConnection-{ACCOUNT_NUMBER}",
            "partition_key":Attribute(
                name="connectionId",
                type=AttributeType.STRING
            ),
            "billing_mode":BillingMode.PAY_PER_REQUEST,
            "encryption":TableEncryption.AWS_MANAGED,
            "removal_policy":RemovalPolicy.DESTROY
            # "read_capacity":5, # enabled if billing mode is PROVISIONED
            # "write_capacity":5, # enabled if billing mode is PROVISIONED
            # "replication_regions":[],
        },
        "global_secondary_index": []
    },
    "users":{
        "table_configuration": {
            "id":f"Users-{ACCOUNT_NUMBER}",
            "table_name":f"Users-{ACCOUNT_NUMBER}",
            "partition_key":Attribute(
                name="userId",
                type=AttributeType.STRING
            ),
            "billing_mode":BillingMode.PAY_PER_REQUEST,
            "encryption":TableEncryption.AWS_MANAGED,
            "removal_policy":RemovalPolicy.DESTROY
            # "read_capacity":5, # enabled if billing mode is PROVISIONED
            # "write_capacity":5, # enabled if billing mode is PROVISIONED
            # "replication_regions":[],
        },
        "global_secondary_index": [
            {
                "partition_key":Attribute(
                    name="organization",
                    type=AttributeType.STRING
                ),
                # "read_capacity":5, # enabled if Table's billing mode is PROVISIONED
                # "write_capacity":5, # enabled if Table's billing mode is PROVISIONED
                "index_name":"organization",
                "projection_type":ProjectionType.ALL # Default
            }
        ]
    }
}