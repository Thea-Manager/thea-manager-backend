#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import getenv, path
from dotenv import load_dotenv

# CDK Imports
from aws_cdk import core as cdk

# local stack imports
from thea_manager_backend.authentication_stack import AuthenticationStack
from thea_manager_backend.realtime_communication_stack import RealtimeCommunicationStack

# ---------------------------------------------------------------
#                           Globals
# ---------------------------------------------------------------
# Current directoy
current_directory = path.dirname(__file__)

# Env vars
load_dotenv(path.join(current_directory, "../.env"))

ACCOUNT_NUMBER=getenv("ACCOUNT_NUMBER")

# ---------------------------------------------------------------
#                       Webservice Stage
# ---------------------------------------------------------------

class RTCWebServiceStage(cdk.Stage):
  def __init__(self, scope: cdk.Construct, id: str, **kwargs):
    super().__init__(scope, id, **kwargs)

    # Authentication webservice
    rtc_service = RealtimeCommunicationStack(self, id)

    # Retrieve url output
    self.api_endpoint = rtc_service.api_endpoint
    
class AuthenticationWebServiceStage(cdk.Stage):
  def __init__(self, scope: cdk.Construct, id: str, **kwargs):
    super().__init__(scope, id, **kwargs)

    # Authentication webservice
    authentication_service = AuthenticationStack(self, id)

    # Retrieve url output
    self.url_output = authentication_service.url_output
