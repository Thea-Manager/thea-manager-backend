#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
import random
from os import getenv, path
from dotenv import load_dotenv

# CDK Imports - DevOps
from aws_cdk import pipelines
from aws_cdk import core as cdk
from aws_cdk import aws_codedeploy as code_deploy 
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as cpactions

# CDK Imports - IAM
from aws_cdk.aws_iam import (
    Role,
    Policy,
    Effect,
    ManagedPolicy,
    PolicyStatement,
    ServicePrincipal
)

# Local package imports
from .webservice_stage import AuthenticationWebServiceStage, RTCWebServiceStage

# ---------------------------------------------------------------
#                             Globals
# ---------------------------------------------------------------

# Current directoy
current_directory = path.dirname(__file__)

# Env vars
load_dotenv(path.join(current_directory, "../.env"))
STAGE=getenv("STAGE")

# AWS Envs
REGION=getenv("REGION")
ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# GitHub envs
REPO_NAME=getenv("REPO_NAME")
REPO_OWNER=getenv("REPO_OWNER")


# ---------------------------------------------------------------
#                          CI/CD Pipeline
# ---------------------------------------------------------------

class RtcCicdPipelineStack(cdk.Stack):
  def __init__(self, scope: cdk.Construct, id: str, **kwargs):
    super().__init__(scope, id, **kwargs)

    ######################################
    #  Create & config deployment stage  #
    ######################################

    # Instantiate artifacts
    self.rtc_source_artifact = codepipeline.Artifact(artifact_name="rtc-source-artifact")
    self.rtc_cloud_assembly_artifact = codepipeline.Artifact(artifact_name="rtc-cloud-assembly-artifact")

    # Instantiate authentication pipeline
    self.rtc_pipeline = pipelines.CdkPipeline(
        scope=self,
        id="serverless-rtc-cicd-pipeline",
        cloud_assembly_artifact=self.rtc_cloud_assembly_artifact,
        pipeline_name="serverless-rtc-cicd-pipeline",
        source_action=cpactions.GitHubSourceAction(
            action_name="serverless-rtc-deployment",
            output=self.rtc_source_artifact,
            oauth_token=cdk.SecretValue.secrets_manager("github-token"),
            owner=REPO_OWNER,
            repo=REPO_NAME,
            trigger=cpactions.GitHubTrigger.POLL
        ),
        synth_action=pipelines.SimpleSynthAction(
            source_artifact=self.rtc_source_artifact,
            cloud_assembly_artifact=self.rtc_cloud_assembly_artifact,
            install_command="npm install -g aws-cdk && pip install -r requirements.txt",
            # build_command="pytest unittests", # Add security scans
            synth_command="cdk synth")
        )

    # Authentication deployment - production
    self.rtc_pipeline.add_application_stage(
        RTCWebServiceStage(
            scope=self, 
            id=STAGE, 
            env={'account': ACCOUNT_NUMBER,'region': REGION}
        )
    )

class AuthenticationCicdPipelineStack(cdk.Stack):
  def __init__(self, scope: cdk.Construct, id: str, **kwargs):
    super().__init__(scope, id, **kwargs)

    ######################################
    #    Authentication CI/CD pipeline   #
    ######################################

    # Instantiate artifacts
    self.authentication_source_artifact = codepipeline.Artifact(artifact_name="authentication-source-artifact")
    self.authentication_cloud_assembly_artifact = codepipeline.Artifact(artifact_name="authentication-cloud-assembly-artifact")

    # Instantiate authentication pipeline
    self.authentication_pipeline = pipelines.CdkPipeline(
        scope=self,
        id="serverless-authentication-cicd-pipeline",
        cloud_assembly_artifact=self.authentication_cloud_assembly_artifact,
        pipeline_name="serverless-authentication-cicd-pipeline",
        source_action=cpactions.GitHubSourceAction(
            action_name="serverless-authentication-deployment",
            output=self.authentication_source_artifact,
            oauth_token=cdk.SecretValue.secrets_manager("github-token"),
            owner=REPO_OWNER,
            repo=REPO_NAME,
            trigger=cpactions.GitHubTrigger.POLL
        ),
        synth_action=pipelines.SimpleSynthAction(
            source_artifact=self.authentication_source_artifact,
            cloud_assembly_artifact=self.authentication_cloud_assembly_artifact,
            install_command="npm install -g aws-cdk && pip install -r requirements.txt",
            # build_command="pytest unittests", # Add security scans
            synth_command="cdk synth")
        )

    # Authentication deployment - production
    self.authentication_pipeline.add_application_stage(
        AuthenticationWebServiceStage(
            scope=self, 
            id=STAGE, 
            env={'account': ACCOUNT_NUMBER,'region': REGION}
        )
    )

class TheaBackendServerCicdPipelineStack(cdk.Stack):
  def __init__(self, scope: cdk.Construct, id: str, **kwargs):
    super().__init__(scope, id, **kwargs)

    ######################################
    #       Configure code deploy        #
    ######################################

    # create application on code deploy
    self.application_server = code_deploy.ServerApplication(
        scope=self, 
        id=f"{STAGE}-thea-backend", 
        application_name=f"{STAGE}-thea-backend"
    )

    # Create deployment group on code deploy
    self.deployment_group = code_deploy.ServerDeploymentGroup(
        scope=self,
        id="code-deployment-group",
        application=self.application_server,
        deployment_group_name="thea-backend-server",
        role=Role(
            scope=self,
            id="deployment-group-role", 
            role_name="code-deployment-group-role",
            assumed_by=ServicePrincipal("codedeploy.amazonaws.com"),
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSCodeDeployRole")
            ]
        ),
        deployment_config=code_deploy.ServerDeploymentConfig.ONE_AT_A_TIME,
        ec2_instance_tags=code_deploy.InstanceTagSet(
            {
                "deployment-group": ["thea-backend-server"]
            }
        ),
    )

    ######################################
    #  Create & configure CICD pipeline  #
    ######################################

    # Instantiate backend server CI/CD pipeline
    self.backend_server_pipeline = codepipeline.Pipeline(
        scope=self,
        id="thea-backend-server-pipeline",
        pipeline_name="thea-backend-server-pipeline",
    )

    # Source stage
    self.source_stage = self.backend_server_pipeline.add_stage(stage_name="Source")     # Declare source stage
    self.source_output = codepipeline.Artifact(artifact_name='Source')                  # Create source artifact output
    self.source_stage.add_action(                                                       # Pull source code from GitHub
        cpactions.GitHubSourceAction(
            action_name="thea-backend-deployment",
            output=self.source_output,
            oauth_token=cdk.SecretValue.secrets_manager("github-token"),
            repo=REPO_NAME,
            owner=REPO_OWNER,
            trigger=cpactions.GitHubTrigger.POLL
        )
    )

    # Deployment stage
    self.deploy_stage = self.backend_server_pipeline.add_stage(stage_name="Deploy")     # Declare deployment stage
    self.deploy_stage.add_action(
        cpactions.CodeDeployServerDeployAction(
            input=self.source_output,
            action_name="deploy-server",
            deployment_group=self.deployment_group
        )
    )
