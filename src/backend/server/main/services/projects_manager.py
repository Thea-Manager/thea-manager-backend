#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# General Imports
import json
from os import getenv

from datetime import date, datetime
from typeguard import check_argument_types

# Utils Imports
from .utils import exception_handler, generate_differences_message

# Local package imports
from ..models.ses import SES
from .workflows import Workflows
from ..models.dynamodb import Dynamo

# Logging Imports
import logging

# ---------------------------------------------------------------
#                       Globals
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                       Project Manager
# ---------------------------------------------------------------


class ProjectsManager:
    """
    Class to programatically manage a project and associated dependencies

    Attributes
    ----------
        _db:
            DynamoDB object instance
        _email:
            SES object client instance

    Methods
    -------
    create_new_project(token, customer_id, project_name, project_type, business_unit, internal_project_owner, \
        internal_client_lead, lead_consulting_partner, consulting_companies, start_date, estimated_end_date, \
        budgeted_cost, currency, team_members, linked_projects, overwrite_generate_code)
        Creates a new unique project

    get_project_information(customer_id, project_id)
        Retrieves unique projects details

    get_project_overview(customer_id, last_evaluated_key)
        Retrieves overview of existing projects

    update_project_info(token, customer_id, project_id, item)
        Updates unique project's information

    add_members(token, customer_id, project_id, team_members)
        Adds new members to a project

    remove_members(token, customer_id, project_id, team_members)
        Removes existing members from a project
    """

    def __init__(self):
        self._db = Dynamo()
        self._email = SES()

    @exception_handler
    def create_new_project(
        self,
        token: str,
        object_id: str,
        customer_id: str,
        project_name: str,
        project_type: str,
        type: str,
        business_unit: str,
        internal_project_owner: dict,
        internal_client_lead: dict,
        lead_consulting_partner: list,
        consulting_companies: str,
        start_date: str,
        estimated_end_date: str,
        budgeted_cost: str,
        currency: str,
        team_members: list,
        linked_projects: list = None,
        overwrite_generate_code: str = "",
    ):
        """
        Enables users to create a new project on the Thea Manager database.

        Parameters:
        -----------
            object_id: str [required]
                unique customer id

            project_id: str [required]
                unique project id

            project_name: str [required]
                project's name

            project_type: str [required]
                project's type

            type: str [required]
                internal or external project

            business_unit: str [required]
                business/legal unit

            consulting_companies: list[str]
                List object containing consulting partner ids

            start_date: str [required]
                start date of the project in the format of YYYY-MM-DD

            end_date: str [required]
                end date of the project in the format of YYYY-MM-DD

            budgeted_cost: str [required]
                project's budgeted cost

            currency: str [required]
                fiscal currency

            lead_consulting_partner: dict
                dictionary: user object for lead consulting partner

            team_members: list[dict] [required]
                Team member names, emails, and user ID

            linked_projects: list[str]  [required]
                list object containing linked project ids

            overwrite_generate_code: str [optional]
                optional project code inputted by user

         Returns:
         --------
            response: str
                server data regarding success/failure of new project creation

            http_status_code: int
                server http status code response
        """

        # Type guarding
        assert check_argument_types()

        # Define target table name
        table_name = f"Projects-{customer_id}"

        # Create Dynamo Object
        logger.info("Creating dynamodb object")
        dynamo_object = {
            "customerId": customer_id,
            "projectId": object_id,
            "code": overwrite_generate_code,
            "projectName": project_name,
            "projectType": project_type,
            "type": type,
            "businessUnit": business_unit,
            "clientLead": internal_client_lead,
            "projectOwner": internal_project_owner,
            "consultingPartners": lead_consulting_partner,
            "consultingCompanies": consulting_companies,
            "status": "active",
            "startDate": start_date,
            "endDate": estimated_end_date,
            "actualEndDate": "",
            "budgetedCost": budgeted_cost,
            "currency": currency,
            "linkedProjects": linked_projects,
            "creationDate": str(date.today()),
            "lastUpdated": str(date.today()),
            "FY": str(date.today().year),
            "scopes": {},
            "progress": "0.0",
            "requestsOverdue": "0.0",
            "outstandingIssues": "0.0",
            "costOverRun": "0.0",
            "costOverRunPer": "0.0",
            "forecastDelay": "0.0",
            "teamMembers": {x["userId"]: x for x in team_members},
            "dataroom": {},
            "analytics": {
                "issues": {
                    "criticality": {
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    },
                    "status": {"open": 0, "closed": 0, "total": 0},
                    "time": {
                        "dueSoon": 0,
                        "dueToday": 0,
                        "overdue": 0,
                    },
                    "natureOfIssue": {},
                },
                "milestones": {
                    "time": {
                        "dueSoon": 0,
                        "dueToday": 0,
                        "overdue": 0,
                    },
                    "status": {"completed": 0, "inProgress": 0, "total": 0},
                },
                "scopes": {
                    "status": {
                        "pending": 0,
                        "rejected": 0,
                        "accepted": 0,
                    },
                    "time": {
                        "dueSoon": 0,
                        "dueToday": 0,
                        "overdue": 0,
                    },
                },
                "documents": {
                    "time": {
                        "dueSoon": 0,
                        "dueToday": 0,
                        "overdue": 0,
                    },
                    "status": {
                        "requested": 0,
                        "submitted": 0,
                        "accepted": 0,
                        "rejected": 0,
                        "total": 0,
                    },
                }
                # "invoices":{
                #     "budget": {
                #         "initialBudget":0,
                #         "revisedBudget":0,
                #         "total":0
                #     },
                #     "invoice": {
                #         "toBeInvoiced":0,
                #         "paidInvoices":0,
                #         "unpaidInvoices":0,
                #         "total":0
                #     }
                # }
            },
            "discussions": {},
        }

        # Create project code
        if not overwrite_generate_code:
            dynamo_object["code"] = dynamo_object["projectId"].upper()[:6]

        # Push to DynamoBD
        logger.info("Adding new project dynamo object to DynamoDB")
        self._db.create_item(table_name, dynamo_object)

        # Send SES identity verification email
        logger.info("Validating team member emails")
        self._email.validate_email([x["email"] for x in team_members])

        # Send Thea signup request email
        logger.info("Sending signup templated email to client team members")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("SIGNUP_TEMPLATE"),
            template_data=json.dumps({"signupLink": getenv("SINGUP_PAGE_LINK")}),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # Send project onboarding email
        logger.info("Sending onboarding templated email to client team members")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("PROJECT_ONBOARD_TEMPLATE"),
            template_data=json.dumps(
                {
                    "organizationId": customer_id,
                    "projectCode": dynamo_object["code"],
                    "projectId": dynamo_object["projectId"],
                    "onboardingPage": getenv("ONBOARDING_PAGE_LINK"),
                }
            ),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # Log workflow
        message = [f"Created project {dynamo_object['code']}"]
        workflow = Workflows.update_workflows(
            token,
            "Create",
            message,
            dynamo_object["projectId"],
            dynamo_object["projectId"],
        )
        self._db.create_item(f"Workflows-{customer_id}", workflow)

        # Return server response
        logger.info("Project created successfully")
        return "Project created successfully", 200

    @exception_handler
    def get_project_information(self, customer_id: str, project_id: str):
        """
        Get information related to a specific project

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                descirption: unique project ID

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

        key = {"projectId": project_id, "customerId": customer_id}

        # Define project expression to get specific keys in data
        projection_expression = ", ".join(
            [
                "projectId",
                "code",
                "projectName",
                "projectType",
                "#type",
                "budgetedCost",
                "currency",
                "businessUnit",
                "projectOwner",
                "clientLead",
                "consultingPartners",
                "consultingCompanies",
                "startDate",
                "teamMembers",
                "progress",
                "requestsOverdue",
                "outstandingIssues",
                "costOverRun",
                "costOverRunPer",
                "forecastDelay",
                "FY",
                "milestones",
                "scopes",
                "issues",
                "endDate",
                "actualEndDate",
                "#status",
            ]
        )

        expression_attribute_names = {"#status": "status", "#type": "type"}

        # Query DynamoDB request
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(
            table_name, key, projection_expression, expression_attribute_names
        )

        if isinstance(response, dict):
            if "scopes" in response.keys():
                response["scopes"] = list(response["scopes"].values())
                response["teamMembers"] = list(response["teamMembers"].values())
                for i in range(len(response["scopes"])):
                    response["scopes"][i]["issues"] = list(
                        response["scopes"][i]["issues"].values()
                    )
                    response["scopes"][i]["reports"] = list(
                        response["scopes"][i]["reports"].values()
                    )
                    response["scopes"][i]["dataroom"] = list(
                        response["scopes"][i]["dataroom"].values()
                    )
                    response["scopes"][i]["milestones"] = list(
                        response["scopes"][i]["milestones"].values()
                    )
                    response["scopes"][i]["teamMembers"] = list(
                        response["scopes"][i]["teamMembers"].values()
                    )

        today_date, due_date = datetime.today(), datetime.strptime(
            response["endDate"], "%Y-%m-%d"
        )

        if today_date > due_date:
            response["delay"] = today_date - due_date
            response["delay"] = response["delay"].total_seconds()
            response["delay"] = int(divmod(response["delay"], 86400)[0])
        else:
            response["delay"] = 0

        # Return server response
        return [response], http_status_code

    @exception_handler
    def get_project_overview(self, customer_id: str, last_evaluated_key: str = None):
        """
        Get projects all projects for a unique and existing customer.

        Parameters:
        -----------
            customer_id: str [required]
                descirption: unique customer ID

            last_evaluated_key: str [optional]
                in case of pagination, last evaluate key is the starting point to the next page

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

        key = {"index_name": "customerId", "index_val": customer_id}

        # Define project expression to get specific keys in data
        projection_expression = ", ".join(
            [
                "projectId",
                "code",
                "projectName",
                "projectType",
                "#type",
                "budgetedCost",
                "currency",
                "businessUnit",
                "consultingCompanies",
                "endDate",
                "startDate",
                "teamMembers",
                "progress",
                "requestsOverdue",
                "outstandingIssues",
                "costOverRun",
                "costOverRunPer",
                "forecastDelay",
                "FY",
                "projectOwner",
                "clientLead",
                "#status",
            ]
        )

        expression_attribute_names = {"#status": "status", "#type": "type"}

        # Get Data
        logger.info("Querying projects overview from DynamoDB")
        projects, code = self._db.read_multiple_items(
            table_name,
            key,
            projection_expression,
            expression_attribute_names,
            last_evaluated_key,
        )

        for i in range(len(projects)):

            today_date, due_date = datetime.today(), datetime.strptime(
                projects[i]["endDate"], "%Y-%m-%d"
            )

            if today_date > due_date:
                projects[i]["delay"] = today_date - due_date
                projects[i]["delay"] = projects[i]["delay"].total_seconds()
                projects[i]["delay"] = int(divmod(projects[i]["delay"], 86400)[0])
            else:
                projects[i]["delay"] = 0

        return projects, code

    @exception_handler
    def update_project_info(
        self, token: str, customer_id: str, project_id: str, item: dict
    ):
        """
        Updates existing unique project's information for existing and unique customer.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            item: dict [required]
                dict containing items to update on DynamoDB

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

        # Query items
        key = {"projectId": project_id, "customerId": customer_id}

        # Check if customer and project exist
        projection_expression = ",".join(
            [
                "projectId",
                "code",
                "projectName",
                "projectType",
                "#type",
                "businessUnit",
                "clientLead",
                "projectOwner",
                "consultingPartners",
                "#status",
                "startDate",
                "endDate",
                "budgetedCost",
                "currency",
                "lastUpdated",
            ]
        )
        expression_attribute_names = {"#status": "status", "#type": "type"}
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        previous_item, _ = self._db.read_single_item(
            table_name, key, projection_expression, expression_attribute_names
        )

        # Update DynamoDB item & update project info
        logger.info("Updating project information on DynamoDB")
        item["lastUpdate"] = str(date.today())
        update_expression = "SET {}".format(", ".join(f"#{k}=:{k}" for k in item))
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
                token, "Update", message, project_id, project_id
            )
            self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("Project information updated successfully")
        return "Project information updated successfully", 200

    @exception_handler
    def add_members(
        self, token: str, customer_id: str, project_id: str, team_members: list
    ):
        """
        Add's new and unique team memebrs to existing project for a unique customer.

        Parameters:
        -----------
            customer_id: str [required]
                unique customer ID

            project_id: str [required]
                unique project ID

            team_members: dict [required]
                dict containing unique team member objects

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

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, _ = self._db.read_single_item(table_name, key, "projectId, code")

        # Get project details
        project_code, project_id = response["code"], response["projectId"]

        # Send SES identity verification email
        logger.info("Vaildating client team member emails")
        self._email.validate_email([x["email"] for x in team_members])

        # Send Thea signup request email
        logger.info("Send signup templated email")
        self._email.send_template_email(
            source=getenv("SOURCE_EMAIL_ADDRESS"),
            template_name=getenv("SIGNUP_TEMPLATE"),
            template_data=json.dumps({"signupLink": getenv("SINGUP_PAGE_LINK")}),
            bcc_addresses=[x["email"] for x in team_members],
        )

        # Send project onboarding email
        logger.info("Send onboarding templated email")
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

        # Add project member
        logger.info("Adding client team members")
        update_expression = "SET {}".format(
            ", ".join(
                [
                    f"teamMembers.#userId_{i} = :{k['userId']}"
                    for i, k in enumerate(team_members)
                ]
            )
        )
        expression_attribute_names = {
            f"#userId_{i}": k["userId"] for i, k in enumerate(team_members)
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
                token, "Add", message, project_id, project_id
            )
            self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info("Successfully add to the project")
        return "Successfully add to the project", 200

    # @exception_handler
    # def remove_members(
    #     self, token: str, customer_id: str, project_id: str, team_members: list
    # ):
    #     """
    #     Removes unique team memebrs from an existing project for a unique customer.

    #     Parameters:
    #     -----------
    #         customer_id: str [required]
    #             unique customer ID

    #         project_id: str [required]
    #             unique project ID

    #         team_members: list [required]
    #             contains user IDs of team members to remove

    #      Returns:
    #      --------

    #         response: str | dict
    #             dict object containing project information

    #         http_status_code: int
    #             http server status response code
    #     """
    #     pass

    #     # Type guarding
    #     assert check_argument_types()

    #     table_name = f"Projects-{customer_id}"

    #     key = {"projectId": project_id, "customerId": customer_id}

    #     # Check if customer and project exist
    #     logger.info(f"Checking if project ID or organization ID exists: {key}")
    #     response, http_status_code =  self._db.read_single_item(table_name, key, "projectId, code")

    #     # Send off-boarding email
    #     logger.info("Send offboarding templated email")
    #     response, http_status_code = self._email.send_template_email(
    #         source = getenv("SOURCE_EMAIL_ADDRESS"),
    #         template_name = getenv("PROJECT_OFFBOARD_TEMPLATE"),
    #         template_data = json.dumps({"projectCode": response["code"]}),
    #         bcc_addresses = [x["email"] for x in team_members.values()])

    #     # Invalidate email address
    #     logger.info("Invalidating client team member emails")
    #     response, http_status_code = self._email.invalidate_email([x["email"] for x in team_members])

    #     # Remove team member from project
    #     update_expression = "REMOVE {}".format(", ".join([f"teamMembers.{k['userId']}" for k in team_members]))

    #     logger.info("Removing client team members from project")
    #     response, http_status_code = self._db.update_item(table_name = table_name, key = key, \
    # update_expression = update_expression, return_values = "UPDATED_NEW")

    #     logger.info("Successfully removed from project", http_status_code)
    #     return "Successfully removed from project", http_status_code
