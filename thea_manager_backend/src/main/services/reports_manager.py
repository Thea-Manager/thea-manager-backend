#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Logging Imports
import logging
logger = logging.getLogger(__name__)

# General Imports
from re import sub
from uuid import uuid4
from pprint import pprint
from datetime import date
from typeguard import check_argument_types

# Utils import
from .utils import exception_handler, generate_differences_message

# Local package imports
from ..models.ses import SES
from .workflows import Workflows
from ..models.dynamodb import Dynamo

# ---------------------------------------------------------------
#                         Configure Logging
# ---------------------------------------------------------------

class ReportsManager():
    """
        Class to programatically manage project reports

        Attributes
        ----------
            _db:
                DynamoDB object instance
            _email:
                SES object client instance

        Methods
        -------
            create_scope_report(token, project_id, customer_id, scope_id, name, due_date, requested_by, submitted_by, description)
                Creates new unique scope report

            get_report_information(customer_id, project_id, scope_id, report_id)
                Retrieves unique report's information

            get_reports_overview(customer_id, project_id, scope_id)
                Retrieves reports overview for unique project

            update_existing_reports(token, customer_id, project_id, items)
                Updates existing report

            delete_existing_reports(customer_id, project_id, reports)
                Deletes existing report
    """

    def __init__(self):
        self._db = Dynamo()
        self._email = SES()

    # TODO: add document reference parameter and object attribute
    @exception_handler
    def create_scope_report(self, token: str, object_id: str, project_id: str, customer_id: str, scope_id: str, name: str, due_date: str, requested_by: dict, submitted_by: dict, description: str):
        """
            Creates new unique scope report

            Parameters:
            -----------

                object_id: str [required]
                    unique object ID
                    
                project_id: str [required]
                    unique project ID

                customer_id: str [required]
                    unique customer ID

                scope_id:  str [required]
                    unique scope ID

                name: str [required]
                    name of repporot

                due_date: str [required]
                    due date to submit report

                requested_by: dict [required]
                    dict object containing requestor details

                submitted_by: dict [required]
                    dict object containing submittor's details             

                str [required]
                    description or details of report

            Returns:
            --------

                response: str | dict
                    str if error responsee, list object containing project information

                http_status_code: int
                    http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        key = {"projectId": project_id, "customerId": customer_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        self._db.read_single_item(table_name, key, "projectId")

        # Create Dynamo object
        dynamo_object = {
            "name": name,
            "dueDate": due_date,
            "requestedBy": requested_by,
            "submittedBy": submitted_by,
            "description": description,
            "status": "pending",
            "created": str(date.today()),
            "lastUpdate": str(date.today()),
            "scopeId": scope_id,
            "reportId": object_id
        }

        # Add project member
        logger.info("Creating new project report")
        update_expression = f"SET scopes.{scope_id}.reports.#reportId = :{dynamo_object['reportId']}"
        expression_attribute_names = {f"#reportId": dynamo_object['reportId']}
        expression_attribute_values = {f":{dynamo_object['reportId']}": dynamo_object}
        self._db.update_item(table_name, key, update_expression, expression_attribute_names, expression_attribute_values)

        # Log workflow
        message = [f"Created new report: {name}"]
        workflow = Workflows.update_workflows(token, "Create", message, project_id, dynamo_object["reportId"])
        self._db.create_item(f"Workflows-{customer_id}", workflow)
        
        logger.info("New project report created successfully")
        return "New project report created successfully", 200

    @exception_handler
    def get_report_information(self, customer_id: str, project_id: str, scope_id: str, report_id: str):
        """
            Get unique report information

            Parameters:
            -----------

                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID

                report_id: str [required]
                    unique report ID

            Returns:
            --------

                response: str | dict
                    str if error responsee, list object containing project information

                http_status_code: int
                    http server status response code
        """

        # Type guarding
        assert check_argument_types()

        key = {"projectId": project_id, "customerId": customer_id}

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Define project expression to get specific keys in data
        projection_expression = f"scopes.{scope_id}.reports.{report_id}"

        # Query DynamoDB request
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code =  self._db.read_single_item(table_name, key, projection_expression)

        if response:
            reports = response["scopes"][scope_id]["reports"]
            if reports:
                return reports[report_id], http_status_code
            else:
                return [], 404
        else:
            # return "Invalid issue or scope ID", 404
            return [], 404

    @exception_handler
    def get_reports_overview(self, customer_id: str, project_id: str, scope_id: str = ""):
        """
            Gets overview of existing reports for unique project

            Parameters:
            -----------

                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    descirption: unique project ID

            Returns:
            --------

                response: str | list
                    str if error, else list object containing project information

                http_status_code: int
                    http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query key
        key = {"customerId": customer_id, "projectId": project_id}

        # Define project expression to get specific keys in data
        if scope_id:
            projection_expression = f"scopes.{scope_id}.reports"
        else:
            projection_expression = "scopes"

        # Get Data
        logger.info("Querying reports overview from DynamoDB")
        response, http_status_code = self._db.read_single_item(table_name, key, projection_expression)
    
        if response:  
            if scope_id:      
                response = list(response["scopes"][scope_id]["reports"].values())
            else:
                reports = []
                for key, val in response["scopes"].items():
                    reports.extend(val["reports"].values())
                response = reports
        else:
            return [], 200

        logger.info(response, http_status_code)
        return response, http_status_code

    @exception_handler
    def update_existing_reports(self, token: str, customer_id: str, project_id: str, items: list):
        """
            Updates reports on the scope manager tool of Thea and stores it on DynamoDB.

            Parameters:
            -----------

                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    descirption: unique project ID

                report_id: str [required]
                    unique scope ID

                items: list
                    dict containing items to update on DynamoDB

            Returns:
            --------

                response: str
                    server response data

                http_staus_code: int
                    descrption: HTTP server response
        """
        
        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"customerId": customer_id, "projectId": project_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code =  self._db.read_single_item(table_name, key, "projectId")

        success, fail = [], []
        for item in items:
            
            scope_id = item["scopeId"]
            report_id = item["reportId"]

            # Query item from DynamoDB
            projection_expression = f"scopes.{scope_id}.reports.{report_id}"
            previous_item, _ = self._db.read_single_item(table_name, key, projection_expression)
            if not previous_item:
                continue
            previous_item = previous_item["scopes"][scope_id]["reports"][report_id]

            # DynamoDB expression & update reports
            logger.info("Updating report details")
            item["lastUpdated"] = str(date.today())
            update_expression = "SET {}".format(", ".join(f"scopes.{scope_id}.reports.{report_id}.#{k}=:{k}" for k in item.keys()))
            expression_attribute_names = {f"#{k}": k for k in item.keys()}
            expression_attribute_values = {f":{k}": v for k, v in item.items()}
            response, http_status_code = self._db.update_item(table_name, key, update_expression, expression_attribute_names, expression_attribute_values)

            # Log workflow
            message = generate_differences_message(previous_item, item)
            if message:
                workflow = Workflows.update_workflows(token, "Update", message, project_id, report_id)
                self._db.create_item(f"Workflows-{customer_id}", workflow)

            if 200 <= http_status_code < 300:
                logger.info(f"Project report updated successfully, {http_status_code}")
                success.append(report_id)
            else:
                logger.error(f"{response}, {http_status_code}")
                fail.append(report_id)


        # Default vavlue
        http_status_code = 200

        if len(success)>=1 and len(fail)==0:
            http_status_code = 200
        elif len(success)==0 and len(fail)>=1:
            http_status_code = 403
        elif len(success)>=1 and len(fail)>=1:
            http_status_code = 405
        else:
            http_status_code = 304

        return {"success": success, "fail": fail}, http_status_code

    @exception_handler
    def delete_existing_reports(self, customer_id: str, project_id: str, reports: list):
        """
            Delete unique existing report for unique customer from the database

            Parameters:
            -----------

                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID

                reports: list [required]
                    list of report IDs to delete on DynamoDB

            Returns:
            --------

                response: str
                    server response data

                http_staus_code: int
                    descrption: HTTP server response
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"customerId": customer_id, "projectId": project_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        self._db.read_single_item(table_name, key, "projectId")

        # DynamoDB expression
        logger.info(f"Deleting project reports {reports}")
        update_expression = "REMOVE {}".format(", ".join([f"reports.{k}" for k in reports]))
        self._db.update_item(table_name = table_name, key = key, update_expression = update_expression, return_values = "UPDATED_NEW")
        
        logger.info(f"Project report deleted successfully")
        return "Project report deleted successfully", 200

if __name__ == "__main__":
    scope_manager = ReportsManager()