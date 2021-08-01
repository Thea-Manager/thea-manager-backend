#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Logging Imports
import logging

logger = logging.getLogger(__name__)

# General Imports
from re import sub

from datetime import date
from os.path import splitext
from typeguard import check_argument_types

# Utils imports
from .utils import convert_size, exception_handler, generate_differences_message
from .utils import accepted_file_extensions

# Local package imports
from ..models.s3 import S3
from .workflows import Workflows
from ..models.dynamodb import Dynamo

# werkzeug imports
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------
#                         Document Manager
# ---------------------------------------------------------------


class DocumentManager:
    """
    Class to programatically interact with AWS S3 via the S3 sub-class
    implementation

    Attributes
    ----------
        _s3
            S3 class object instance to interact with boto3 APIs

        -db
            dynamodb class object instance to interact with boto3 APIs

    Methods
    -------
        document_request(customer_id, project_id, scope_id, requested_by, requested_of, doc_attributes)
            Creates a document request

        presigned_url_get(customer_id, project_id, scope_id, filename, version_id)
            Generates presigned URL to download object from S3

        presigned_url_post(customer_id, project_id, scope_id, filename, document_id)
            Generates presigned URL to uploadd object to S3

        update_document_details(token, customer_id, project_id, items)
            Updates document details on DynamoDB

        get_data_room_contents(customer_id, project_id, scope_id, filename)
            Retrieves contents of a directory including list of all files or a file's versions
    """

    def __init__(self) -> None:
        self._s3 = S3()
        self._db = Dynamo()

    @exception_handler
    def document_request(
        self,
        token: str,
        object_id: str,
        customer_id: str,
        project_id: str,
        requested_by: dict,
        requested_of: dict,
        name: str,
        due_date: str,
        description: str,
    ):
        """
        Creates a new document reference and request, then appends that it to target
        scope on DynamoDB

        Parameters:
        -----------
            object_id: str [required]
                unique object ID

            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                 unique project ID

            scope_id: str [required]
                 unique project ID

            requested_by: dict [required]
                dict containing details regarding user requesting document

            requested_of: dict [required]
                dict containing details regarding document requestee user

            doc_attributes: dict [required]
                document attributes

        Returns:
        --------
            response: str
                success or error message of doc creation request

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"customerId": customer_id, "projectId": project_id}

        # Create dynamodb object
        dynamo_object = {
            "status": "requested",
            "requestedOf": requested_of,
            "requestedBy": requested_by,
            "docReqId": object_id,
            "name": name,
            "dueDate": due_date,
            "description": description,
        }

        # DynamoDB expressions
        update_expression = f"SET dataroom.#docReqId = :{dynamo_object['docReqId']}"
        expression_attribute_names = {"#docReqId": dynamo_object["docReqId"]}
        expression_attribute_values = {f":{dynamo_object['docReqId']}": dynamo_object}

        # Create new milestone
        logger.info("Creating new document request")
        self._db.update_item(
            table_name,
            key,
            update_expression,
            expression_attribute_names,
            expression_attribute_values,
        )

        # Log workflow
        message = [f"Created document request {dynamo_object['docReqId']}"]
        workflow = Workflows.update_workflows(
            token, "Create", message, project_id, dynamo_object["docReqId"]
        )
        self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("New document request created successfully")
        return "New document request created successfully", 200

    @exception_handler
    def document_request_overview(
        self, customer_id: str, project_id: str, doc_req_id: str = ""
    ):
        """
        Gets list of existing document requests

        Parameters
        ----------

            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            doc_req_id: str [optional]
                unique document request Id

        Returns
        -------

            response: list
                list of document request objects

            http_status_code: int
                http server status response code
        """
        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Key
        key = {"customerId": customer_id, "projectId": project_id}

        # Define project expression to get specific keys in data
        if doc_req_id:
            projection_expression = f"dataroom.{doc_req_id}"
        else:
            projection_expression = "dataroom"

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(
            table_name, key, projection_expression
        )

        if response:
            if doc_req_id:
                return response["dataroom"][doc_req_id], http_status_code
            else:
                return list(response["dataroom"].values()), http_status_code
        else:
            return [], 200

    @exception_handler
    def presigned_url_get(
        self,
        customer_id: str,
        project_id: str,
        item_id: str,
        filename: str,
        version_id: str = "",
    ):
        """
        Generates secure and expiring presigned URL to get document to S3 bucket

        Parameters:
        -----------

            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                 unique project ID

            scope_id: str [required]
                 unique project ID

            filename: str [required]
                 secure filename

            version_id: str [optional]
                version ID of object. Defaults to latest version if null

        Returns:
        --------
            response: str | None
                presigned URL | error message

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"customerId": customer_id, "projectId": project_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        self._db.read_single_item(table_name, key, "projectId")[0]

        # Generate presigned url
        url = self._s3.create_presigned_url(
            version_id=version_id,
            object_name="/".join([project_id, item_id, filename]),
            bucket_name=customer_id,
        )[0]

        return url, 200

    @exception_handler
    def presigned_url_post(
        self,
        token: str,
        customer_id: str,
        project_id: str,
        filenames: list,
        item_id: str,
        metadata: dict = None,
    ):
        """
        Generates secure and expiring presigned URL to push document to S3 bucket

        Parameters:
        -----------

            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            scope_id: str [required]
                unique project ID

            filename: str [required]
                secure filename

            version_id: str [optional]
                version ID of object. Defaults to latest version if null

        Returns:
        --------
            response: str | None
                presigned URL | error message

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        metadata = [metadata] * len(filenames)

        # Generate presigned url
        presigned_urls = []
        for i, name in enumerate(filenames):

            # Get file name and extension
            name, extension = splitext(name)

            # Default values
            url, accepted_file_format, secured_name = None, False, name

            # Secure file name & generate url
            if extension in accepted_file_extensions:

                accepted_file_format = True

                secured_name = secure_filename(name) + extension

                kwargs = {
                    "bucket_name": customer_id,
                    "object_name": "/".join([project_id, item_id, secured_name]),
                    "upload": True,
                    "metadata": metadata[i],
                }

                url = self._s3.create_presigned_url(**kwargs)

            presigned_urls.append(
                {
                    "presignedUrl": url,
                    "orignalName": name,
                    "securedName": secured_name,
                    "acceptedFileFormat": accepted_file_format,
                }
            )

            # Log workflow
            message = [f"Uploaded document {name} to {customer_id}"]
            workflow = Workflows.update_workflows(
                token, "Add", message, project_id, secured_name
            )
            self._db.create_item(f"Workflows-{customer_id}", workflow)

        return presigned_urls, 200

    @exception_handler
    def update_request_document_details(
        self, token: str, customer_id: str, project_id: str, items: list
    ):
        """
        Updates existing document details on DynamoDB

        Parameters:
        -----------

            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                 unique project ID

            items: list [required]
                list containing items to update on DynamoDB

        Returns:
        --------
            response: str
                dict object containing project information

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"projectId": project_id, "customerId": customer_id}

        for item in items:

            # Extract doc attributes
            doc_request_id = item["docReqId"]

            # Query item from DynamoDB
            previous_item = self._db.read_single_item(
                table_name, key, f"dataroom.{doc_request_id}"
            )[0]
            if not previous_item:
                continue
            previous_item = previous_item["dataroom"][doc_request_id]

            # Define DynamoDB expressions & update doc details
            logger.info(f"Updating document request {doc_request_id}")
            item["lastUpdate"] = str(date.today())
            update_expression = "SET {}".format(
                ", ".join(f"dataroom.{doc_request_id}.#{k}=:{k}" for k in item.keys())
            )
            expression_attribute_names = {f"#{k}": k for k in item.keys()}
            expression_attribute_values = {f":{k}": v for k, v in item.items()}
            self._db.update_item(
                table_name,
                key,
                update_expression,
                expression_attribute_names,
                expression_attribute_values,
            )

        # Log workflow
        message = generate_differences_message(previous_item, item)
        if message:
            workflow = Workflows.update_workflows(
                token, "Update", message, project_id, doc_request_id
            )
            self._db.create_item(f"Workflows-{customer_id}", workflow)

        return f"Updated {doc_request_id} successfully", 200

    @exception_handler
    def get_data_room_contents(
        self, customer_id: str, project_id: str, item_id: str = ""
    ):
        """
        Get's dictionary of a bucket's contents

        Parameters:
        -----------

            customer_id: str [required]
                unique customer ID

            project_id: str [optional]
                 unique project ID

            scope_id: str [optional]
                 unique project ID

            filename: str [optional]
                document's filename

        Returns:
        --------
            response: dict | str
                list of versions or error message of doc creation request

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # Generate prefix
        prefix = "/".join(list(filter(None, [project_id, item_id])))

        response, https_status_code = self._s3.list_files(customer_id, prefix)

        for i in range(len(response)):
            response[i].pop("ETag")
            response[i].pop("StorageClass")

            # Get object versions
            versions = self._s3.list_file_versions(customer_id, response[i]["Key"])[0]
            response[i]["Versions"] = []
            for j, version in enumerate(versions):
                response[i]["Versions"].append(
                    {
                        "IsLatest": version["IsLatest"],
                        "Size": convert_size(version["Size"]),
                        "VersionNumber": f"V{len(versions) - j}",
                        "VersionId": version["VersionId"],
                    }
                )

            # Get object meta data
            metadata = self._s3.get_object_metadata(customer_id, response[i]["Key"])[0]
            for key, val in metadata.items():
                if "x-amz-meta-" in key:
                    response[i][sub("x-amz-meta-", "", key)] = val

            # Generate object high-level attribuutes
            keys = response[i]["Key"].split("/")
            response[i]["projectId"] = keys[0]
            response[i]["itemId"] = keys[1]
            response[i]["Key"] = keys[-1]
            response[i]["Size"] = convert_size(response[i]["Size"])

        return response, https_status_code
