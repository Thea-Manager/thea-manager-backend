#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import getenv, path
from dotenv import load_dotenv

# CDK Imports
from aws_cdk import pipelines
from aws_cdk import core as cdk
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as cpactions

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

class AuthenticationCicdPipelineStack(cdk.Stack):
  def __init__(self, scope: cdk.Construct, id: str, **kwargs):
    super().__init__(scope, id, **kwargs)

    ######################################
    #    Authentication CI/CD pipeline   #
    ######################################

    # Instantiate artifacts
    self.authentication_source_artifact = codepipeline.Artifact(artifact_name="authentication-source-artifact")
    self.authentication_cloud_assembly_artifact = codepipeline.Artifact(artifact_name="authentication-cloud-assembly-artifact")

    # Instanticate authentication pipeline
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

class RtcCicdPipelineStack(cdk.Stack):
  def __init__(self, scope: cdk.Construct, id: str, **kwargs):
    super().__init__(scope, id, **kwargs)

    ######################################
    #  Create & config deployment stage  #
    ######################################

    # Instantiate artifacts
    self.rtc_source_artifact = codepipeline.Artifact(artifact_name="rtc-source-artifact")
    self.rtc_cloud_assembly_artifact = codepipeline.Artifact(artifact_name="rtc-cloud-assembly-artifact")

    # Instanticate authentication pipeline
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
