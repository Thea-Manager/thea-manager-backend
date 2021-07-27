#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Logging Imports
import logging
logger = logging.getLogger(__name__)

# Native & External imports
from os import getenv
from typeguard import check_argument_types

# Boto3 Imports
from boto3 import client

# Utils imports 
from .utils import exception_handler
# ---------------------------------------------------------------
#                           AWS SES
# ---------------------------------------------------------------

class SES():

    def __init__(self) -> None:
        self._ses = client("ses", region_name = getenv("REGION"))
        self._exceptions = self._ses.exceptions

    @exception_handler
    def send_template_email(self, source: str, template_name: str, template_data: str, bcc_addresses: list):      
        """
            Sends pre-defined template as an email to validated email addresses.

            Parameters:
            -----------
                source:
                    type: str [required]
                    description: sender email address

                template_name:
                    type: str [required]
                    description: name of the pre-defined template

                bcc_addresses:
                    type: list [required]
                    description: list of validated email addresses

            Returns:
            --------

                response: null | str
                    null if success, str if error raised

                http_status_code: int
                    server status response code

            Raises
            ------

                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()

        # try:
        logger.info(f"Sending templated email")
        response = self._ses.send_templated_email(
            Source = source,
            Destination = {"BccAddresses": bcc_addresses},
            Template = template_name,
            TemplateData = template_data)

        logger.info(f"{None}, {response['ResponseMetadata']['HTTPStatusCode']}")
        return None, response["ResponseMetadata"]["HTTPStatusCode"]
   
    # TODO: need to add capability to validate email domain list
    # TODO: need to add capability to valdiate email address regex format
    @exception_handler
    def validate_email(self, email_addresses: list):
        """
            Validates and adds email addresses from a client-side provided email list

            Parameters:
            -----------
                email_addresses:
                    type: list
                    description: list of email addresses to validate & add

            Returns:
            --------
                response: null | str
                    null if success, str if error raised

                http_status_code: int
                    server status response code

            Raises
            ------
                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()

        # TODO: figure out a way to check if emails is verified without
        logger.info("Getting list of verified emaills")
        verified_emails = self._ses.list_identities(IdentityType = "EmailAddress")
        
        logger.info("Retrieved verified emaills")
        verified_emails = verified_emails["Identities"]

        # Send verification emails to unverified identities
        logger.info("Sending verification emails")
        for email in set(email_addresses):
            logger.info(f"Sending verification email to {email}")
            self._ses.verify_email_identity(EmailAddress = email)

        return None, 200

    @exception_handler
    def invalidate_email(self, email_addresses: list):
        """
            Invalidates and removes email addresses from the SES validated email list

            Parameters:
            -----------
                email_addresses:
                    type: list
                    description: list of email addresses to remove

            Returns:
            --------
                response: null | str
                    null if success, str if error raised

                http_status_code: int
                    server status response code

            Raises
            ------
                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()

        logger.info("Invalidating emails identities")
        for email in email_addresses:
            logger.info(f"Invalidating email: {email}")
            self._ses.delete_verified_email_address(EmailAddress = email)
        return None, 200


if __name__ == "__main__":

    email = SES()

