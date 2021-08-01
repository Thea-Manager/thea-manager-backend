#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# General imports
from os import getenv
from datetime import date
from typeguard import check_argument_types

# Utils import
from .utils import exception_handler, generate_differences_message

# Local package imports
from ..models.ses import SES
from .workflows import Workflows
from ..models.dynamodb import Dynamo

# Native Imports
import json
import logging

# ---------------------------------------------------------------
#                               Globals
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                           Issue Tracker
# ---------------------------------------------------------------


class IssuesTracker:
    """
    Class to programatically manage a project's issues

    Attributes
    ----------
        _db:
            DynamoDB object client instance
        _email:
            SES object client instance

    Methods
    -------
    create_new_milestone(token, customer_id, project_id, scope_id, issue_name, region, business_unit, \
        date_of_raise, due_date, nature_of_issue, criticality, issue_str, impact_value, currency, impact_on, \
        document_ref, issue_owner, resolution_path)
        Creates new project milestone

    get_milestone_details(customer_id, project_id, scope_id, milestone_id)
        Retrieves unique milestone's details

    get_milestone_oveerview(customer_id, project_id, scope_id)
        Retrieves milestone overview

    update_existing_milestone(token, customer_id, project_id, milestones)
        Updates existing milestone deetails
    """

    def __init__(self):
        self._db = Dynamo()
        self._email = SES()

    # TODO: When implementing UUID, delete the multiple projection expressions in this method
    @exception_handler
    def create_new_issue(
        self,
        token: str,
        object_id: str,
        customer_id: str,
        project_id: str,
        scope_id: str,
        issue_name: str,
        region: str,
        business_unit: str,
        date_of_raise: str,
        due_date: str,
        nature_of_issue: str,
        criticality: str,
        issue_description: str,
        impact_value: str,
        currency: str,
        impact_on: str,
        document_ref: dict,
        issue_owner: dict,
        resolution_path: str,
    ):
        """
        Creates a new issue on the issue tracker tool of Thea and stores it on DynamoDB.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            scope_id: str [requried]
                unique scope's id

            issue_name: str [requried]
                descrption: name of issue

            region: str [required]
                regional location of customer

            business_unit: str [required]
                customer business unit or department

            date_of_raise:  str [required]
                date the issue was raised to stakeholders

            due_date: str [required]
                due date of issue to close it

            nature_of_issue: str [required]
                nature of issue being raised

            criticality: str [required]
                criticality/sevirity of issue being raised

            issue_str [required]
                description of issue being raised

            impact_value: str [required]
                financial value or magnitude of the impact being caused by issue

            currency: str [required]
                descrition: fisical currency of the finanical impact caused by issue

            impact_on: str [required]
                business unit or department being impacted by issue

            document_ref:  dict [required]
                JSON object containing object reference and details with regards to reference document being uploaded
                object_params:
                    DocumentUrl: url location of document
                    VersionId: version ID of the document stored
                    DateAdded: date the document was stored

            issue_owner: dict [required]
                JSON object containing object reference and details regarding assigned team leader
                object_params:
                    user_type: type of user
                    user_name: name of user
                    user_email: user email
                    display_name: user display name
                    picture_url: url to user display picture
                    authorized_by: jSON object containing reference and details regarding authorizer

            resolution_path: str [required]
                description of how to resolve the current outstanding issue


        Returns:
        --------
            response: None | str
                null if success | str if error raised

            https_status_code: int
                http status server response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: make table name environment variable
        table_name = f"Projects-{customer_id}"

        # Key
        key = {"projectId": project_id, "customerId": customer_id}

        # Projection Expression
        projection_expression = ", ".join(["projectId", "code"])

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, _ = self._db.read_single_item(table_name, key, projection_expression)

        # Get project code
        project_code = response["code"]

        # Request body
        dynamo_object = {
            "scopeId": scope_id,
            "issueName": issue_name,
            "region": region,
            "businessUnit": business_unit,
            "dateOfRaise": date_of_raise,
            "dueDate": due_date,
            "natureOfIssue": nature_of_issue,
            "criticality": criticality,
            "issueDescription": issue_description,
            "status": "open",
            "impactValue": impact_value,
            "currency": currency,
            "impactOn": impact_on,
            "documentRef": document_ref,
            "issueOwner": issue_owner,
            "resolutionPath": resolution_path,
            "lastUpdated": str(date.today()),
            "issueId": object_id,
        }

        # Send project onboarding email
        logger.info("Sending project onboarding email")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("ISSUE_ASSIGNMENT_TEMPLATE"),
            template_data=json.dumps(
                {
                    "issueId": f'"{dynamo_object["issueName"]}"',
                    "projectCode": project_code,
                }
            ),
            bcc_addresses=[issue_owner["email"]],
        )

        # Dynamo update expressions & update
        logger.info("Create new project issue")
        update_expression = (
            f"SET scopes.#scopeId.issues.#IssueId = :{dynamo_object['issueId']}"
        )
        expression_attribute_names = {
            "#scopeId": scope_id,
            "#IssueId": dynamo_object["issueId"]
        }
        expression_attribute_values = {f":{dynamo_object['issueId']}": dynamo_object}
        self._db.update_item(
            table_name,
            key,
            update_expression,
            expression_attribute_names,
            expression_attribute_values,
        )

        # Log workflow
        message = [f"Created new issue: {issue_name}"]
        workflow = Workflows.update_workflows(
            token, "Create", message, project_id, dynamo_object["issueId"]
        )
        self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("New issue created successfully")
        return "New issue created successfully", 200

    @exception_handler
    def get_issue_details(
        self, customer_id: str, project_id: str, scope_id: str, issues_id: str
    ):
        """
        Get detailed breakdown information on a specific issue on the issue tracker tool of Thea.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            issues_id: str [required]
                unique issue ID

        Returns:
        --------
            response: str | list
                dict object containing project information

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # Query Items
        key = {"projectId": project_id, "customerId": customer_id}

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Define project expression to get specific keys in data
        projection_expression = f"scopes.{scope_id}.issues.{issues_id}"

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(
            table_name, key, projection_expression
        )

        if response:
            issues = response["scopes"][scope_id]["issues"]
            if issues:
                return issues[issues_id], http_status_code
        else:
            # return "Invalid issue or scope ID", 404
            return [], 404

    @exception_handler
    def get_issues_overview(
        self, customer_id: str, project_id: str, scope_id: str = ""
    ):
        """
        Get an overview of all existing issues related to a particular project.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

        Returns:
        --------
            response: str | list
                dict object containing project information

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # Query Keys
        key = {"projectId": project_id, "customerId": customer_id}

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Define project expression to get specific keys in data
        if scope_id:
            projection_expression = f"scopes.{scope_id}.issues"
        else:
            projection_expression = "scopes"

        # Get data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, _ = self._db.read_single_item(table_name, key, projection_expression)

        if response:
            if scope_id:
                return list(response["scopes"][scope_id]["issues"].values()), 200
            else:
                issues = []
                for key, val in response["scopes"].items():
                    issues.extend(val["issues"].values())
                return issues, 200
        else:
            return [], 200

    @exception_handler
    def update_existing_issue(
        self, token: str, customer_id: str, project_id: str, items: list
    ):
        """
        Updates existing issue on the issue tracker tool of Thea and stores it on DynamoDB.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            issues_id: str [required]
                unique issue ID

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

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(
            table_name, key, "projectId"
        )

        success, fail = [], []
        for item in items:

            scope_id = item["scopeId"]
            issues_id = item["issueId"]

            # Query item from DynamoDB
            projection_expression = f"scopes.{scope_id}.issues.{issues_id}"
            previous_item, _ = self._db.read_single_item(
                table_name, key, projection_expression
            )

            if not previous_item:
                continue

            previous_item = previous_item["scopes"][scope_id]["issues"][issues_id]

            # Define DynamoDB expressions & update issue
            logger.info(f"Updating issue {issues_id}")
            item["lastUpdate"] = str(date.today())
            update_expression = "SET {}".format(
                ", ".join(
                    f"scopes.{scope_id}.issues.{issues_id}.#{k}=:{k}"
                    for k in item.keys()
                )
            )
            expression_attribute_names = {f"#{k}": k for k in item.keys()}
            expression_attribute_values = {f":{k}": v for k, v in item.items()}
            response, http_status_code = self._db.update_item(
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
                    token, "Update", message, project_id, issues_id
                )
                self._db.create_item(f"Workflows-{customer_id}", workflow)

            if 200 <= http_status_code < 300:
                logger.info(
                    f"Issue {issues_id}'s details successfully updated, {http_status_code}"
                )
                success.append(issues_id)
            else:
                logger.error(f"{response}, {http_status_code}")
                fail.append(issues_id)

        # Determine status codes

        # Default vavlue
        http_status_code = 200

        if len(success) >= 1 and len(fail) == 0:
            http_status_code = 200
        elif len(success) == 0 and len(fail) >= 1:
            http_status_code = 403
        elif len(success) >= 1 and len(fail) >= 1:
            http_status_code = 405
        else:
            http_status_code = 304

        return {"success": success, "fail": fail}, http_status_code

    @exception_handler
    def delete_existing_issues(
        self, token: str, customer_id: str, project_id: str, issues: list
    ):
        """
        Delete unique existing issues for unique customer from the database

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            issues: list [required]
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

        # DynamoDB expression & delete
        logger.info(f"Deleting project issues {issues}")
        update_expression = "REMOVE {}".format(
            ", ".join([f"issues.{k}" for k in issues])
        )
        self._db.update_item(
            table_name=table_name,
            key=key,
            update_expression=update_expression,
            return_values="UPDATED_NEW",
        )

        # Log workflow
        for issue_id in issues:
            message = f"deleted issue {issue_id}"
            workflow = Workflows.update_workflows(
                token, "Delete", message, project_id, issue_id
            )
            self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("Project issues deleted successfully")
        return "Project issues deleted successfully", 200
