#!/usr/bin/env python

#TODO: Configure CORS to be more secure and limiting only to the domain you care about

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

    def __init__(self, scope: cdk.Construct, construct_id: str, vpc_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ######################################
        #      Create & lambda handlers      #
        ######################################

        # Connection route handler, alias, and IAM roles
        self.connect_handler = lmb.Function(
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
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            environment={"CUSTOMER_ID":ACCOUNT_NUMBER},
            vpc=vpc_stack.vpc,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/connect"))
        )
        
        self.connect_alias = lmb.Alias(
            scope=self,
            version=self.connect_handler.current_version,
            id=f"{STAGE}-websocket-on-connect-alias",
            alias_name="websocket-on-connect-alias",
        )

        self.connect_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.DENY,
                resources=["*"],
                not_actions=[
                    "apigateway:POST",
                    "dynamodb:PutItem",
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                    "ec2:AssignPrivateIpAddresses",
                    "ec2:UnassignPrivateIpAddresses"
                ]
            )
        )

        self.connect_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.ALLOW,
                resources=["*"],
                actions=[
                    "apigateway:POST",
                    "dynamodb:PutItem"
                ]
            )
        )

        # Disconnection route handler & alias
        self.disconnect_handler = lmb.Function(
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
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            environment={"CUSTOMER_ID":ACCOUNT_NUMBER},
            vpc=vpc_stack.vpc,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/disconnect"))
        )

        self.disconnect_alias = lmb.Alias(
            scope=self,
            version=self.disconnect_handler.current_version,
            id=f"{STAGE}-websocket-on-disconnect-alias",
            alias_name="websocket-on-disconnect-alias",
        )

        self.disconnect_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.DENY,
                resources=["*"],
                not_actions=[
                    "apigateway:POST",
                    "dynamodb:DeleteItem",
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                    "ec2:AssignPrivateIpAddresses",
                    "ec2:UnassignPrivateIpAddresses"
                ]
            )
        )

        self.disconnect_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.ALLOW,
                resources=["*"],
                actions=[
                    "apigateway:POST",
                    "dynamodb:DeleteItem"
                ]
            )
        )

        # Default connection route handler & alias
        self.default_handler = lmb.Function(
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
            vpc=vpc_stack.vpc,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/default"))
        )

        self.default_alias = lmb.Alias(
            scope=self,
            version=self.default_handler.current_version,
            id=f"{STAGE}-websocket-on-default-alias",
            alias_name="websocket-on-default",
        )

        # Send message route handler & alias
        self.send_message_handler = lmb.Function(
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
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            vpc=vpc_stack.vpc,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/message"))
        )
        
        self.send_message_alias = lmb.Alias(
            scope=self,
            version=self.send_message_handler.current_version,
            id=f"{STAGE}-websocket-send-message-alias",
            alias_name="websocket-send-message",
        )

        self.send_message_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.DENY,
                resources=["*"],
                not_actions=[
                    "dynamodb:Scan",
                    "dynamodb:PutItem",
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                    "ec2:AssignPrivateIpAddresses",
                    "ec2:UnassignPrivateIpAddresses"
                ]
            )
        )

        self.send_message_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.ALLOW,
                resources=["*"],
                actions=[
                    "dynamodb:Scan",
                    "dynamodb:PutItem"
                ]
            )
        )

        # Discussions route handler & alias
        self.discussions_handler = lmb.Function(
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
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                    ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                ]
            ),
            environment={"CUSTOMER_ID":ACCOUNT_NUMBER},
            vpc=vpc_stack.vpc,
            timeout=cdk.Duration.minutes(15),
            code=lmb.Code.from_asset(path.join(current_directory, "lambdas/realtime-communication/discussions"))
        )
        
        self.discussions_alias = lmb.Alias(
            scope=self,
            version=self.discussions_handler.current_version,
            id=f"{STAGE}-websocket-discussions-alias",
            alias_name="websocket-discussions",
        )

        self.discussions_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.DENY,
                resources=["*"],
                not_actions=[
                    "dynamodb:Scan",
                    "dynamodb:PutItem",
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                    "ec2:AssignPrivateIpAddresses",
                    "ec2:UnassignPrivateIpAddresses"
                ]
            )
        )

        self.discussions_handler.add_to_role_policy(
            PolicyStatement(
                effect=Effect.ALLOW,
                resources=["*"],
                actions=[
                    "dynamodb:Scan",
                    "dynamodb:PutItem"
                ]
            )
        )

        ######################################
        #   Create & configure API Gateway   #
        ######################################

        # Create websocket api gateway with default routes
        self.websocket_api_gateway = WebSocketApi(
            scope=self, 
            id="serverless-realtime-communication",
            api_name="serverless-realtime-communication",
            connect_route_options={"integration": LambdaWebSocketIntegration(handler=self.connect_handler)},
            disconnect_route_options={"integration": LambdaWebSocketIntegration(handler=self.disconnect_handler)},
            default_route_options={"integration": LambdaWebSocketIntegration(handler=self.default_handler)}
        )

        # Add custom routes to websocket api gateway
        self.websocket_api_gateway.add_route(
            route_key="message",
            integration=LambdaWebSocketIntegration(
                handler=self.send_message_handler
            )
        )

        self.websocket_api_gateway.add_route(
            route_key="discussions",
            integration=LambdaWebSocketIntegration(
                handler=self.discussions_handler
            )
        )

        ######################################
        #  Config per lambda failure Alarms  #
        #   create timed canary deployment   #
        ######################################

        # Zipped alias name & function
        zipped = [
            (f"{STAGE}-connect-alias", self.connect_alias),
            (f"{STAGE}-disconnect-alias", self.disconnect_alias),
            (f"{STAGE}-default-alias", self.default_alias),
            (f"{STAGE}-send-message-alias", self.send_message_alias),
            (f"{STAGE}-discussions-alias", self.discussions_alias),
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
        #             Add env vars           #
        ######################################

        self.discussions_handler.add_environment(
            key="WEBSOCKET_ENDPOINT",
            value=self.websocket_api_gateway.api_endpoint
        )