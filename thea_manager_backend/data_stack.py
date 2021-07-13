#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# CDK Imports
from aws_cdk import core as cdk
from aws_cdk.aws_dynamodb import Table
from aws_cdk.aws_s3 import Bucket, BucketEncryption, CorsRule, HttpMethods

# Utils imports
from .utils import dynamodb_configurations

# ---------------------------------------------------------------
#                           Custom VPC
# ---------------------------------------------------------------

class CdkDataStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ######################################
        # Create & Configure DynamoDB Tables #
        ######################################

        self.dynamo_tables={}

        for table, configuration in dynamodb_configurations.items():

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
            removal_policy=cdk.RemovalPolicy.DESTROY,
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
        

        ######################################
        #              CFN Output            #
        ######################################
        
        cdk.CfnOutput(
            scope=self,
            id="Output",
            value=f"data-stack-{construct_id}"
        )
