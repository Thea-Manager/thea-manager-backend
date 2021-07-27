#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import getenv
from dotenv import load_dotenv

# CDK Imports - Core
from aws_cdk.core import cdk

# CDK Imports - DynamoDB
from aws_cdk.aws_dynamodb import (
    Table,
    Attribute,
    AttributeType,
    BillingMode,
    TableEncryption,
    ProjectionType
)

# CDK Imports - S3
from aws_cdk.aws_s3 import Bucket, BucketEncryption, CorsRule, HttpMethods

# ---------------------------------------------------------------
#                        Env variables
# ---------------------------------------------------------------

# Load env vars
load_dotenv()
ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# ---------------------------------------------------------------
#                           Custom VPC
# ---------------------------------------------------------------

class CdkDataStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ######################################
        # Create & Configure DynamoDB Tables #
        ######################################
        
        # Dynamo table configurations
        self.dynamodb_configurations={
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
                    "removal_policy":cdk.RemovalPolicy.DESTROY
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
                    "removal_policy":cdk.RemovalPolicy.DESTROY
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
                    "removal_policy":cdk.RemovalPolicy.DESTROY
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
                    "removal_policy":cdk.RemovalPolicy.DESTROY
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
                    "removal_policy":cdk.RemovalPolicy.DESTROY
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

        # Apply table configurations
        self.dynamo_tables={}

        for table, configuration in self.dynamodb_configurations.items():

            # Create and set table configurations
            self.dynamo_tables[table]=Table(self, **configuration["table_configuration"])

            if configuration["global_secondary_index"]:
                for config in configuration["global_secondary_index"]:
                    self.dynamo_tables[table].add_global_secondary_index(**config)

        ######################################
        #    Create & Configure S3 Buckets   #
        ######################################

        self.s3_buckets=Bucket(
            scope=self,
            id=f"{construct_id}-s3-bucket",
            bucket_name=f"{construct_id}-s3-bucket",
            removal_policy=cdk.cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            # server_access_logs_prefix="bucket-access-logs",
            versioned=True,
            cors=[
                CorsRule(
                    allowed_methods=[
                        HttpMethods.GET,
                        HttpMethods.POST
                    ],
                    allowed_origins=[
                        "*"
                    ],
                    allowed_headers=[
                        "x-amz-meta-upload-date",
                        "x-amz-meta-document-name",
                        "x-amz-meta-description",
                        "x-amz-meta-attached-by",
                        "Content-Type",
                        "Authorization",
                        "Date",
                        "x-amz-content-sha256",
                        "x-amz-date",
                        "x-amz-security-token",
                    ]
                )
            ]
        )