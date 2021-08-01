#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
from os import getenv

# External imports
from typeguard import check_argument_types

# Boto3 Imports
from boto3 import client

# Utils imports
from .utils import exception_handler

# Logging Imports
import logging

# ---------------------------------------------------------------
#                            Globals
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                               S3
# ---------------------------------------------------------------


class S3:
    """
    This class is to programtically interact with the boto3 S3 API.

    Attributes
    ----------

    _s3_client: class 'botocore.client.s3', required

    Methods
    -------
    create_presigned_url(bucket_name, object_name, upload, version_id, expiration)
        Generates presigned expiring url to upload/download files from S3

    list_files(bucket_name, prefix, page_size, max_keys, starting_token)
        Lists files present in an S3 directory

    list_file_versions(bucket_name, prefix)
        Lists file versions for a file (if versioning is enabled on a bucket)

    delete_file(bucket_name, key, version_id)
        Deletes file from S3 bucket
    """

    # TODO: Set these vars as part of config env vars
    def __init__(self) -> None:
        self._s3_client = client("s3", region_name=getenv("REGION"))

    @exception_handler
    def create_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        version_id: str = "",
        upload: bool = False,
        expiration: int = 600,
        metadata: dict = None,
    ):
        """
        Generate a presigned URL S3 POST request to upload a file

        Parameters
        -----------
            bucket_name: str [required]
                s3 bucket name

            object_name: str [required]
                s3 object name

            upload: bool [required]
                Bool statement to either upload or download

            version_id: str [optional], default = ""
                version_id of object. If null, the last version is retrieved

            expiration: int [optional], default = 60
                Time in seconds for the presigned URL to remain valid

        Returns
        -----------
            response: dict, with the following keys:
                url: URL to post to
                fields: Dictionary of form fields and values to submit with the POST

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

        # Generate a presigned S3 POST URL
        if not upload:
            # Create target params dictionary
            if not version_id:
                target_params = {"Bucket": bucket_name, "Key": object_name}
            else:
                target_params = {
                    "Bucket": bucket_name,
                    "Key": object_name,
                    "VersionId": version_id,
                }
            response = self._s3_client.generate_presigned_url(
                "get_object", Params=target_params, ExpiresIn=expiration
            )
        else:
            if metadata:
                conditions = [{k: v} for k, v in metadata.items()]
            else:
                conditions = None

            kwargs = {
                "Bucket": bucket_name,
                "Key": object_name,
                "ExpiresIn": expiration,
                "Fields": metadata,
                "Conditions": conditions,
            }

            kwargs = {k: v for k, v in kwargs.items() if v}
            response = self._s3_client.generate_presigned_post(**kwargs)
        return response, 200

    @exception_handler
    def list_files(
        self,
        bucket_name: str,
        prefix: str,
        page_size: int = 50,
        max_keys: int = 10000,
        starting_token: str = None,
    ):
        """
        List files in a bucket.

        Parameters
        -----------
            bucket_name: str [required]
                bucket to upload file to

            prefix: str [required]
                prefix representing subfolder path

            page_size: str [required]
                size of pagination response

            max_keys: int [optional]
                maximum number of files to retrieve

            starting_token: str [optional]
                token id indicating position of last item in pagination list

        Returns
        -----------
            contents: list
                List of file contents

            http_status_code: int
                http server response status code

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

        paginator = self._s3_client.get_paginator("list_objects_v2")
        response = list(
            paginator.paginate(
                Bucket=bucket_name,
                Prefix=prefix,
                PaginationConfig={
                    "MaxItems": max_keys,
                    "PageSize": page_size,
                    "StartingToken": starting_token,
                },
            )
        )

        # Http status code
        http_status_code = response[0]["ResponseMetadata"]["HTTPStatusCode"]

        # Contents
        if "Contents" in response[0]:
            contents = response[0]["Contents"]
        else:
            contents = []

        return contents, http_status_code

    @exception_handler
    def list_file_versions(self, bucket_name: str, prefix: str):
        """
        List a file's versions.

        Parameters
        -----------
            bucket_name: str [required]
                bucket to upload file to

            prefix: str [required]
                prefix representing subfolder path

        Returns
        -----------
            versions: list
                List of file contents

            http_status_code: int
                http server response status code

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
        response = self._s3_client.list_object_versions(
            Bucket=bucket_name, Prefix=prefix
        )
        return response["Versions"], response["ResponseMetadata"]["HTTPStatusCode"]

    @exception_handler
    def get_object_metadata(
        self, bucket_name: str, object_name: str, version_id: str = None
    ):
        """
        Retrieves object related metadata from S3

        Parameters
        ----------

            bucket_name: str [required]
                S3 bucket name

            object_name: str [required]
                S3 object name

            version_id: str [required]
                S3 object version ID (requries bucket versioning to be enabled)

        Returns
        -------

            metadata: dict
                http headers containing object metadata

            http_status_code: int
                http server response status code

        Raises
        ------
            ClientError
                Boto3 client service related error when making API request

            ParamValidationError
                Error is raised when incorrect parameters provided to boto3
                API method
        """
        assert check_argument_types()
        kwargs = {"Bucket": bucket_name, "Key": object_name, "VersionId": version_id}
        kwargs = {k: v for k, v in kwargs.items() if v}
        response = self._s3_client.head_object(**kwargs)
        return (
            response["ResponseMetadata"]["HTTPHeaders"],
            response["ResponseMetadata"]["HTTPStatusCode"],
        )

    @exception_handler
    def delete_file(self, bucket_name: str, key: str, version_id: str = ""):
        """
        Deletes file in S3 bucket subfolder.

        Parameters
        -----------
            bucket_name: str [required]
                bucket to upload file to

            key: str [required]
                file bucket location

            version_id: str [required]
                version id of file

        Returns
        -----------
            response: null

            http_status_code: int
                http server response status code

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

        kwargs = {"Bucket": bucket_name, "Key": key, "VersionId": version_id}

        kwargs = {k: v for k, v in kwargs.items() if v}
        response = self._s3_client.delete_object(**kwargs)
        return None, response["ResponseMetadata"]["HTTPStatusCode"]
