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
# from thea_manager_backend.ecs_no_vpc_stack import CdkEcsStack


# from thea_manager_backend.ec2_stack import CdkEc2Stack
# from thea_manager_backend.data_stack import CdkDataStack

# # CI/CD Stack Imports
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
# Infrastructure only stacks
vpc_stack = CdkVpcStack(app, f"vpc-{ACCOUNT_NUMBER}", env=environment)
ecs_stack = CdkEcsStack(app, f"ecs-{ACCOUNT_NUMBER}", vpc_stack, env=environment)
# data_stack = CdkDataStack(app, f"databases-{ACCOUNT_NUMBER}", env=environment)

# ecs_stack = CdkEcsStack(app, f"ecs-no-custom-vpc-{ACCOUNT_NUMBER}", env=environment)

# Application related stacks
# rtc_stack = RtcCicdPipelineStack(app, id=f"serverless-rtc-{ACCOUNT_NUMBER}", env=environment)
# authentication_stack = AuthenticationCicdPipelineStack(app, id=f"serverless-authentication-{ACCOUNT_NUMBER}", env=environment)
# thea_backend_server_stack = TheaBackendServerCicdPipelineStack(app, id=f"thea-backend-server-{ACCOUNT_NUMBER}", env=environment)

# Declare dependencies
ecs_stack.add_dependency(vpc_stack)
# thea_backend_server_stack.add_dependency(ecs_stack)

# ---------------------------------------------------------------
#                Generate CloudFormation Template
# ---------------------------------------------------------------

app.synth()