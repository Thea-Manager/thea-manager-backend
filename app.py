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
from thea_manager_backend.ec2_stack import CdkEc2Stack
from thea_manager_backend.data_stack import CdkDataStack
from thea_manager_backend.cicd_pipeline_stack import AuthenticationCicdPipelineStack, RtcCicdPipelineStack

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

# Declare stack instances
# Infrastructure only stacks
vpc_stack = CdkVpcStack(app, f"vpc-{ACCOUNT_NUMBER}", env=environment)
CdkEc2Stack(app, f"ec2-{ACCOUNT_NUMBER}", vpc_stack, env=environment)
CdkDataStack(app, f"databases-{ACCOUNT_NUMBER}", env=environment)

# Application related stacks
RtcCicdPipelineStack(app, id=f"serverless-rtc-{ACCOUNT_NUMBER}", env=environment)
AuthenticationCicdPipelineStack(app, id=f"serverless-authentication-{ACCOUNT_NUMBER}", env=environment)

# ---------------------------------------------------------------
#                Generate CloudFormation Template
# ---------------------------------------------------------------

app.synth()