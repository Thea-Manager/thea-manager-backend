#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native Imports
from os import getenv
from datetime import datetime, date
from typeguard import check_argument_types

# Utils imports
from .utils import exception_handler, generate_differences_message

# Local package imports
from ..models.ses import SES
from .workflows import Workflows
from ..models.dynamodb import Dynamo

# Native Imports
import json
import logging

# ---------------------------------------------------------------
#                         Globals
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                         Scope Manager
# ---------------------------------------------------------------


class ScopeManager:
    """
    Class to programatically manage a projec's scopes

    Attributes
    ----------
        _db:
            DynamoDB object instance
        _email:
            SES object client instance

    Methods
    -------
    create_new_scope(token, customer_id, project_id, scope_name, start_date, end_date, \
        consultant, total_fees, billing_schedule, engagement_letter_ref, team_memberstoken, customer_id, project_id, scope_name, start_date, end_date, consultant, total_fees, billing_schedule, engagement_letter_ref, team_members)

    get_scope_details(customer_id, project_id, scope_id)

    get_scopes_overview(customer_id, project_id)

    update_scope_details(token, customer_id, project_id, items)

    delete_scope(customer_id, project_id, scopes)

    add_scope_members(token, customer_id, project_id, scope_id, team_members)

    remove_scope_members(token, customer_id, project_id, scope_id, team_members)
    """

    def __init__(self):
        self._db = Dynamo()
        self._email = SES()

    # TODO: need to update structure of billing schedule
    @exception_handler
    def create_new_scope(
        self,
        token: str,
        object_id: str,
        customer_id: str,
        project_id: str,
        scope_name: str,
        start_date: str,
        end_date: str,
        consultant: dict,
        total_fees: str,
        billing_schedule: str,
        engagement_letter_ref: dict,
        team_members: list,
    ):
        """
        This method enables authorized users to create a new scope on the Thea Manager database.

        Parameters:
        -----------

            object_id: str [required]
                unique object ID

            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            scope_name: str [required]
                name of the scope

            start_date:  str [required]
                project start date

            end_date: str [required]
                estiamted end date of the project

            consultant: str [required]
                email address of consultant project leader

            total_fees: float [required]
                strnigifyed float of project's budgeted cost

            billing_schedule str [required]
                string object as placeholder for billing schedule

            engagement_letter_ref dict [required]
                dict object containing reference information regarding the scope's engagement letter

            team_members dict [required]
                dict of objects containing team member emails

        Returns:
        --------
            response: str
                server response data

            http_staus_code: int
                HTTP server response
        """

        # Type guarding
        assert check_argument_types()

        # Reference vars
        today = datetime.today()

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
        project_code, project_id = response["code"], response["projectId"]

        # Create dynamo object
        dynamo_object = {
            "scopeId": object_id,
            "scopeName": scope_name,
            "creationDate": str(today),
            "lastUpdated": str(today),
            "startDate": start_date,
            "endDate": end_date,
            "consultant": consultant,
            "totalFees": total_fees,
            "engagementLetterRef": engagement_letter_ref,
            "billingSchedule": billing_schedule,
            "status": "pending",
            "teamMembers": {x["userId"]: x for x in team_members},
            "issues": {},
            "milestones": {},
            "dataroom": {},
            "reports": {},
        }

        # Send SES identity verification email
        logger.info("Validating email addresses")
        self._email.validate_email([x["email"] for x in team_members])

        # Send Thea signup request email
        logger.info("Sending signup templated email to consultant team members")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("SIGNUP_TEMPLATE"),
            template_data=json.dumps({"signupLink": getenv("SINGUP_PAGE_LINK")}),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # Send project onboarding email
        logger.info("Sending onboarding templated email to consultant team members")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("PROJECT_ONBOARD_TEMPLATE"),
            template_data=json.dumps(
                {
                    "projectId": project_id,
                    "projectCode": project_code,
                    "organizationId": customer_id,
                    "onboardingPage": getenv("ONBOARDING_PAGE_LINK"),
                }
            ),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # DynamoDB expressions
        logger.info("Creating new project scope")
        update_expression = f"SET scopes.#scopeId = :{dynamo_object['scopeId']}"
        expression_attribute_names = {"#scopeId": dynamo_object["scopeId"]}
        expression_attribute_values = {f":{dynamo_object['scopeId']}": dynamo_object}
        self._db.update_item(
            table_name,
            key,
            update_expression,
            expression_attribute_names,
            expression_attribute_values,
        )

        # Log workflow
        message = [f"Created scope {dynamo_object['scopeName']}"]
        workflow = Workflows.update_workflows(
            token, "Create", message, project_id, dynamo_object["scopeId"]
        )
        self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("New scope created successfully")
        return "New scope created successfully", 200

    @exception_handler
    def get_scope_details(self, customer_id: str, project_id: str, scope_id: str):
        """
        Get a unique scope's details on the scope manager tool of Thea.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            scope_id: str [required]
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

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"customerId": customer_id, "projectId": project_id}

        # Define project expression to get specific keys in data
        projection_expression = ", ".join(
            [
                f"scopes.{scope_id}.scopeId",
                f"scopes.{scope_id}.scopeName",
                f"scopes.{scope_id}.totalFees",
                f"scopes.{scope_id}.endDate",
                f"scopes.{scope_id}.startDate",
                f"scopes.{scope_id}.#status",
                f"scopes.{scope_id}.teamMembers",
                f"scopes.{scope_id}.lastUpdated",
            ]
        )

        expression_attribute_names = {"#status": "status"}

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(
            table_name, key, projection_expression, expression_attribute_names
        )
        if response:
            response = list(response["scopes"].values())[0]
            response["teamMembers"] = list(response["teamMembers"].values())
            return response, http_status_code
        else:
            return "Invalid scope ID", 404

    @exception_handler
    def get_scopes_overview(self, customer_id: str, project_id: str):
        """
        Get scope details on the scope manager tool of Thea.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

        Returns:
        --------
            response: str or list
                server response data
            http_staus_code: int
                descrption: HTTP server response
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Key
        key = {"customerId": customer_id, "projectId": project_id}

        # Define project expression to get specific keys in data
        projection_expression = "scopes"

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(
            table_name, key, projection_expression
        )

        tmp = []
        for key, val in response["scopes"].items():
            val.pop("issues")
            val.pop("reports")
            val.pop("dataroom")
            val.pop("milestones")
            val.pop("billingSchedule")
            val.pop("creationDate")
            val.pop("teamMembers")
            val.pop("lastUpdated")
            val.pop("consultant")
            tmp.append(val)

        logger.info(f"{tmp}, {http_status_code}")
        return tmp, http_status_code

    # TODO: Need to add check to prevent updating issues, milestones, and reports
    @exception_handler
    def update_scope_details(
        self, token, customer_id: str, project_id: str, items: list
    ):
        """
        Updates scopes on the scope manager tool of Thea and stores it on DynamoDB.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            items: list
                dict containing items to update on DynamoDB

        Returns:
        --------
            response: str
                server response data

            http_staus_code: int
                HTTP server response
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        # Query items
        key = {"customerId": customer_id, "projectId": project_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(
            table_name, key, "projectId"
        )

        success, fail = [], []
        for item in items:

            scope_id = item["scopeId"]

            # Query item from DynamoDB
            projection_expression = f"scopes.{scope_id}"
            previous_item, _ = self._db.read_single_item(
                table_name, key, projection_expression
            )
            if not previous_item:
                continue
            previous_item = previous_item["scopes"][scope_id]

            # DynamoDB expression & update scope
            logger.info(f"Updating scope's {scope_id}")
            item["lastUpdated"] = str(date.today())
            update_expression = "SET {}".format(
                ", ".join(f"scopes.{scope_id}.#{k}=:{k}" for k in item.keys())
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
                    token, "Update", message, project_id, scope_id
                )
                self._db.create_item(f"Workflows-{customer_id}", workflow)

            if 200 <= http_status_code < 300:
                logger.info(
                    f"Project information updated successfully, {http_status_code}"
                )
                success.append(scope_id)
            else:
                logger.error(f"{response}, {http_status_code}")
                fail.append(scope_id)

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
    def delete_scope(self, customer_id: str, project_id: str, scopes: list):
        """
        Delete unique existing scope for unique customer from the database

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            scopes: list[str] [required]
                list of scope IDs to delete

        Returns:
        --------
            response: str
                server response data

            http_staus_code: int
                HTTP server response
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

        # DynamoDB expression & delete scope
        logger.info(f"Delete project scopes {scopes}")
        update_expression = "REMOVE {}".format(
            ", ".join([f"scopes.{k}" for k in scopes])
        )
        self._db.update_item(
            table_name=table_name,
            key=key,
            update_expression=update_expression,
            return_values="UPDATED_NEW",
        )

        logger.info("Project scope deleted successfully")
        return "Project scope deleted successfully", 200

    @exception_handler
    def add_scope_members(
        self,
        token: str,
        customer_id: str,
        project_id: str,
        scope_id: str,
        team_members: list,
    ):
        """
        Add's new and unique team memebrs to existing project for a unique customer.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            team_members: list [required]
                list containing unique team member objects

        Returns:
        --------
            response: str | dict
                dict object containing project information

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        key = {"projectId": project_id, "customerId": customer_id}

        projection_expression = ", ".join(["projectId", "code"])

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, _ = self._db.read_single_item(table_name, key, projection_expression)

        # Get project details
        project_code, project_id = response["code"], response["projectId"]

        # Send SES identity verification email
        logger.info("Validating team member emails")
        self._email.validate_email([x["email"] for x in team_members])

        # Send Thea signup request email
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("SIGNUP_TEMPLATE"),
            template_data=json.dumps({"signupLink": getenv("SINGUP_PAGE_LINK")}),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # Send project onboarding email
        logger.info("Sending onboarding templated email to consultant team members")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("PROJECT_ONBOARD_TEMPLATE"),
            template_data=json.dumps(
                {
                    "projectId": project_id,
                    "projectCode": project_code,
                    "organizationId": customer_id,
                    "onboardingPage": getenv("ONBOARDING_PAGE_LINK"),
                }
            ),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # DynamoDB expression
        logger.info("Adding new scope members")
        update_expression = "SET {}".format(
            ", ".join(
                [
                    f"scopes.{scope_id}.teamMembers.#memberId_{i} = :{k['userId']}"
                    for i, k in enumerate(team_members)
                ]
            )
        )
        expression_attribute_names = {
            f"#memberId_{i}": k["userId"] for i, k in enumerate(team_members)
        }
        expression_attribute_values = {f":{x['userId']}": x for x in team_members}
        self._db.update_item(
            table_name,
            key,
            update_expression,
            expression_attribute_names,
            expression_attribute_values,
        )

        # Log workflow
        message = [
            f"Added {member['name']} ({member['email']})" for member in team_members
        ]
        if message:
            workflow = Workflows.update_workflows(
                token, "Add", message, project_id, scope_id
            )
            # kwargs["key"], kwargs["table_name"] = key, table_name
            self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("Successfully added to the project")
        return "Successfully added to the project", 200

    @exception_handler
    def remove_scope_members(
        self,
        token: str,
        customer_id: str,
        project_id: str,
        scope_id: str,
        team_members: list,
    ):
        """
        Remove's unique team memebrs to existing project for a unique customer.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            team_members: list [required]
                list containing unique team member objects

        Returns:
        --------
            response: str | dict
                dict object containing project information

            http_status_code: int
                http server status response code
        """

        # Type guarding
        assert check_argument_types()

        table_name = f"Projects-{customer_id}"

        key = {"projectId": project_id, "customerId": customer_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, _ = self._db.read_single_item(table_name, key, "projectId, code")

        # Send off-boarding email
        logger.error("Sending project offboarding email to consultant team members")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("PROJECT_OFFBOARD_TEMPLATE"),
            template_data=json.dumps({"projectCode": response["code"]}),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # Invalidate email address
        logger.error("Invalidating user emails")
        self._email.invalidate_email([x["email"] for x in team_members])

        # Remove team member from project
        logger.info("Removing scope members")
        update_expression = "REMOVE {}".format(
            ", ".join(
                [f"scopes.{scope_id}.teamMembers.{k['userId']}" for k in team_members]
            )
        )
        self._db.update_item(
            table_name=table_name,
            key=key,
            update_expression=update_expression,
            return_values="UPDATED_NEW",
        )

        # Log workflow
        message = [
            f"removed {member['name']} ({member['email']})" for member in team_members
        ]
        if message:
            workflow = Workflows.update_workflows(
                token, "Remove", message, project_id, scope_id
            )
            self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("Successfully removed from project")
        return "Successfully removed from project"
