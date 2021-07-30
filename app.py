#!/usr/bin/env python3

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import getenv
from dotenv import load_dotenv

# cdk imports
from aws_cdk import core as cdk

# local stack imports
from thea_manager_backend.vpc_stack import CdkVpcStack
from thea_manager_backend.ecs_stack import CdkEcsStack
from thea_manager_backend.data_stack import CdkDataStack
from thea_manager_backend.authentication_stack import AuthenticationStack
from thea_manager_backend.realtime_communication_stack import RealtimeCommunicationStack

# CI/CD Stack Imports
# from thea_manager_backend.cicd_pipeline_stack import (
#     RtcCicdPipelineStack,
#     AuthenticationCicdPipelineStack,
#     TheaBackendServerCicdPipelineStack
# )

# ---------------------------------------------------------------
#                        Env variables
# ---------------------------------------------------------------

# Load env vars
load_dotenv()

REGION=getenv("REGION")
ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# ---------------------------------------------------------------
#                        Configurations
# ---------------------------------------------------------------

environment = cdk.Environment(account=ACCOUNT_NUMBER, region=REGION)

# ---------------------------------------------------------------
#                        CDK Entry Point
# ---------------------------------------------------------------

# Declare app instance
app = cdk.App()

# Declare stacks
vpc_stack = CdkVpcStack(app, f"vpc-{ACCOUNT_NUMBER}", env=environment)
ecs_stack = CdkEcsStack(app, f"ecs-{ACCOUNT_NUMBER}", vpc_stack, env=environment)
database_stack = CdkDataStack(app, f"databases-{ACCOUNT_NUMBER}", env=environment)
authentication_stack = AuthenticationStack(app, f"authentication-{ACCOUNT_NUMBER}", vpc_stack, env=environment)
rtc_stack = RealtimeCommunicationStack(app, f"realtime-communication-{ACCOUNT_NUMBER}", vpc_stack, env=environment)

# Define dependencies
ecs_stack.add_dependency(vpc_stack)
database_stack.add_dependency(ecs_stack)
rtc_stack.add_dependency(database_stack)
authentication_stack.add_dependency(database_stack)

# ---------------------------------------------------------------
#                Generate CloudFormation Template
# ---------------------------------------------------------------

app.synth()