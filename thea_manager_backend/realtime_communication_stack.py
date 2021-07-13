#!/usr/bin/env python

#TODO: Configure CORS to be more secure and limiting only to the domain you care about

#TODO: For each lambda function, first create a default role only for lambdas with the service 
# principal focused on lambda. Then add a role using the add_role method to add apigateway related
# roles with the service principal focused on apigateway.amazonaws.com

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import path, getenv
from dotenv import load_dotenv

# CDK imports
from aws_cdk import core as cdk
from aws_cdk.aws_iam import (
    Role,
    Effect,
    ManagedPolicy,
    PolicyDocument,
    PolicyStatement,
    ServicePrincipal)

from aws_cdk.aws_apigatewayv2 import WebSocketApi
from aws_cdk.aws_apigatewayv2_integrations import LambdaWebSocketIntegration

import aws_cdk.aws_lambda as lmb
import aws_cdk.aws_codedeploy as codedeploy
import aws_cdk.aws_cloudwatch as cloudwatch

# ---------------------------------------------------------------
#                             Globals
# ---------------------------------------------------------------

# Current directoy
current_directory = path.dirname(__file__)

# Env vars
load_dotenv(path.join(current_directory, "../.env"))

STAGE=getenv("STAGE")
ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# ---------------------------------------------------------------
#                Serverless Realtime Communication
# ---------------------------------------------------------------


class RealtimeCommunicationStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        ######################################
        #      Create & lambda handlers      #
        ######################################

        # Connection route handler & alias
        connect_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-websocket-on-connect-handler",
            function_name=f"{STAGE}-websocket-on-connect",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            description="Websocket connection handler",
            role=Role(
                scope=self,
                id="websocket-on-connect-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "websocket-on-connect":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "dynamodb:*",
                                    "apigateway:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "apigateway:POST",
                                    "dynamodb:PutItem"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            environment={"CUSTOMER_ID":ACCOUNT_NUMBER},
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/connect")))
        
        connect_alias = lmb.Alias(
            scope=self,
            version=connect_handler.current_version,
            id=f"{STAGE}-websocket-on-connect-alias",
            alias_name="websocket-on-connect-alias",
        )

        # Disconnection route handler & alias
        disconnect_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-websocket-on-disconnect-handler",
            function_name=f"{STAGE}-websocket-on-disconnect",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            description="Websocket default route to handle disconnection",
            role=Role(
                scope=self,
                id="websocket-on-disconnect-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "websocket-on-disconnect":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "dynamodb:*",
                                    "apigateway:*"
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "apigateway:POST",
                                    "dynamodb:DeleteItem"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            environment={"CUSTOMER_ID":ACCOUNT_NUMBER},
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/disconnect")))

        disconnect_alias = lmb.Alias(
            scope=self,
            version=disconnect_handler.current_version,
            id=f"{STAGE}-websocket-on-disconnect-alias",
            alias_name="websocket-on-disconnect-alias",
        )

        # Default connection route handler & alias
        default_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-websocket-on-default-connection-handler",
            function_name=f"{STAGE}-websocket-on-default",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            role=Role(
                scope=self,
                id="websocket-on-default-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/default")))

        default_alias = lmb.Alias(
            scope=self,
            version=default_handler.current_version,
            id=f"{STAGE}-websocket-on-default-alias",
            alias_name="websocket-on-default",
        )

        # Send message route handler & alias
        send_message_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-websocket-send-message-handler",
            function_name=f"{STAGE}-websocket-send-message",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            description="Websocket send message handler",
            role=Role(
                scope=self,
                id="websocket-send-message-handler-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "websocket-send-message":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "dynamodb:*",
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "dynamodb:Scan",
                                    "dynamodb:PutItem"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/message")))
        
        send_message_alias = lmb.Alias(
            scope=self,
            version=send_message_handler.current_version,
            id=f"{STAGE}-websocket-send-message-alias",
            alias_name="websocket-send-message",
        )

        # Discussions route handler & alias
        discussions_handler = lmb.Function(
            scope=self,
            id=f"{STAGE}-websocket-discussions-handler",
            function_name=f"{STAGE}-websocket-discussions",
            handler="handler.handler",
            runtime=lmb.Runtime.PYTHON_3_8,
            description="Websocket send message handler",
            role=Role(
                scope=self,
                id="websocket-discussions-role",
                assumed_by=ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "websocket-discussions":PolicyDocument(
                        statements=[
                            PolicyStatement(
                                effect=Effect.DENY,
                                actions=[
                                    "dynamodb:*",
                                ],
                                resources=["*"]
                            ),
                            PolicyStatement(
                                effect=Effect.ALLOW,
                                actions=[
                                    "dynamodb:Scan",
                                    "dynamodb:PutItem"
                                ],
                                resources=["*"]
                            ),
                        ]
                    )
                },
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            environment={"CUSTOMER_ID":ACCOUNT_NUMBER},
            #vpc=vpc_stack,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/discussions")))
        
        discussions_alias = lmb.Alias(
            scope=self,
            version=discussions_handler.current_version,
            id=f"{STAGE}-websocket-discussions-alias",
            alias_name="websocket-discussions",
        )

        ######################################
        #   Create & configure API Gateway   #
        ######################################

        # Create websocket api gateway with default routes
        self.websocket_api_gateway = WebSocketApi(
            scope=self, 
            id="serverless-realtime-communication",
            api_name="serverless-realtime-communication",
            connect_route_options={"integration": LambdaWebSocketIntegration(handler=connect_handler)},
            disconnect_route_options={"integration": LambdaWebSocketIntegration(handler=disconnect_handler)},
            default_route_options={"integration": LambdaWebSocketIntegration(handler=default_handler)}
        )

        # Add custom routes to websocket api gateway
        self.websocket_api_gateway.add_route(
            route_key="message",
            integration=LambdaWebSocketIntegration(
                handler=send_message_handler
            )
        )

        self.websocket_api_gateway.add_route(
            route_key="discussions",
            integration=LambdaWebSocketIntegration(
                handler=discussions_handler
            )
        )

        ######################################
        #  Config per lambda failure Alarms  #
        #   create timed canary deployment   #
        ######################################

        # Zipped alias name & function
        zipped = [
            (f"{STAGE}-connect-alias", connect_alias),
            (f"{STAGE}-disconnect-alias", disconnect_alias),
            (f"{STAGE}-default-alias", default_alias),
            (f"{STAGE}-send-message-alias", send_message_alias),
            (f"{STAGE}-discussions-alias", discussions_alias),
        ]

        for name, alias in zipped:

            # Alarm configuration 
            failure_alarm = cloudwatch.Alarm(
                scope=self, 
                id=name,
                metric=cloudwatch.Metric(
                    metric_name="5XXError",
                    namespace=f"AWS/ApiGateway/RealtimeCommunication/{name}",
                    dimensions={"ApiName": "serverless-realtime-communication"},
                    statistic="Sum",
                    period=cdk.Duration.minutes(1)),
                threshold=1,
                evaluation_periods=1)

            # Canary deployment
            codedeploy.LambdaDeploymentGroup(
                scope=self,
                id=f"{name}-DeploymentGroup",
                alias=alias,
                deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_10_MINUTES,
                alarms=[failure_alarm])


        ######################################
        #      Create API gateway URL ref    #
        ######################################

        # Create reference for serverless authentication API gateway
        self.api_endpoint = cdk.CfnOutput(
            scope=self,
            value=self.websocket_api_gateway.api_endpoint,
            id="websocket-realtime-communication-api-endpoint", 
        )