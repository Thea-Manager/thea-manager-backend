#!/usr/bin/env python

# ---------------------------------------------------------------
#                              Imports
# ---------------------------------------------------------------

# Logging Imports
import logging
logger = logging.getLogger(__name__)

# General imports
from pprint import pprint
from datetime import datetime, date
from typeguard import check_argument_types

# Utils import
from .utils import exception_handler, generate_differences_message

# Local package imports
from .workflows import Workflows
from ..models.dynamodb import Dynamo

# ---------------------------------------------------------------
#                        Milestones Manager
# ---------------------------------------------------------------

class MilestonesManager():
    """
        Class to programatically manage a project's milestones

        Attributes
        ----------
            _db:
                DynamoDB object instance

        Methods
        -------
        create_new_milestone(token, customer_id, project_id, scope_id, milestone_name, start_date, end_date, phase, assignee, notes, business_unit, currency, invoiceable, cost)
            Creates new milestone in a unique project scope

        get_milestone_details(customer_id, project_id, scope_id, milestone_id)
            Get information related to a unique project's milestone

        get_milestone_overview(customer_id, project_id, scope_id)
            Get scope details on the scope manager tool of Thea

        update_existing_milestone(token, customer_id, project_id, milestones)
            Updates an existing milestone  
    """

    def __init__(self):
        self._db = Dynamo()

    @exception_handler
    def create_new_milestone(self, token: str, object_id: str, customer_id: str, project_id: str, scope_id: str, milestone_name: str, start_date: str, end_date: str, phase: str, assignee: dict, notes: str = "", business_unit: str = "", currency: str = "", invoiceable: bool = False, cost: str = "0.0"):
        """
            Creates a new milestone on the milestone manager tool of Thea and stores it on DynamoDB.

            Parameters:
            -----------

                object_id: str [required]
                    unique object ID

                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                     unique project ID

                scope_id: str [required]
                    unique scope ID

                milestone_name: str [required]
                    name of milestone

                start_date: str [required]
                    date project start date

                end_date: str [required]
                    estiamted end date of the project

                phase: str [required]
                    name of milestone phase

                project_manager: str [required]
                    name | email of project manager

                assignee: str [required]
                    name | email of assignee

                invoiceable: float [required]
                    invoiceable cost of associated milestone
                
                notes: str [optional]
                    note describing milestone

                business_unit: str [optional]
                    name of business unit

                currency: str [optional]
                    name of currency type

                invoiceable: bool [optional]
                    milestone invoiceable or not

                cost: str [optional]
                    stringifyed float cost of invoice

             Returns:
             --------
                response: str | list
                    dict object containing project information

                http_status_code: int
                    http server status response code
        """
        
        # Type guarding
        assert check_argument_types()

        # TODO: make table name environment variable
        table_name = f"Projects-{customer_id}"

        # Key
        key = {"projectId": project_id, "customerId": customer_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        self._db.read_single_item(table_name, key, "projectId")
            
        # Create dynamo object
        dynamo_object = {
            "status": "pending",
            "scopeId": scope_id,
            "milestoneName": milestone_name,
            "creationDate": str(datetime.today()),
            "startDate": start_date,
            "endDate": end_date,
            "phase": phase,
            "assignee": assignee,
            "invoiceable": invoiceable,
            "cost": cost,
            "currency": currency,
            "businessUnit": business_unit,
            "notes": notes,
            "discussion": "0",
            "milestoneId":object_id
        }

        # DynamoDB expressions
        logger.info("Creating new milestone")
        update_expression = f"SET scopes.#scopeId.milestones.#milestoneId = :{dynamo_object['milestoneId']}"        
        expression_attribute_names = {"#milestoneId": dynamo_object['milestoneId'], "#scopeId": scope_id}
        expression_attribute_values = {f":{dynamo_object['milestoneId']}": dynamo_object}
        self._db.update_item(table_name, key, update_expression, expression_attribute_names, expression_attribute_values)

        # Log workflow
        message = [f"Created new milestone: {milestone_name}"]
        workflow = Workflows.update_workflows(token, "Create", message, project_id, dynamo_object["milestoneId"])
        self._db.create_item(f"Workflows-{customer_id}", workflow)

        logger.info(f"New milestone created successfully")
        return "New milestone created successfully", 200

    @exception_handler
    def get_milestone_details(self, customer_id: str, project_id: str, scope_id: str, milestone_id: str):
        """
            Get information related to a unique project's milestone

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID
            
                milestone_id: str [required]
                    unique milestone ID

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
        projection_expression = f"scopes.{scope_id}.milestones.{milestone_id}"

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(table_name, key, projection_expression)

        if response:
            milestones = response["scopes"][scope_id]["milestones"]
            if not milestones:
                logger.error(f"Milestone ID not found, 404")
                return "Milestone ID not found", 404
            else:
                return milestones[milestone_id], http_status_code
        else:
            # return "Invalid scope or milestone ID", 404
            return [], 404

    @exception_handler
    def get_milestones_overview(self, customer_id: str, project_id: str, scope_id: str = ""):
        """
            Get scope details on the scope manager tool of Thea.

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID

                scope_id: str [optional]
                    unique scope ID

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

        # Key
        key = {"customerId": customer_id, "projectId": project_id}

        # Define project expression to get specific keys in data
        if scope_id:
            projection_expression = f"scopes.{scope_id}.milestones"
        else:
            projection_expression = "scopes"

        # Get Data
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code = self._db.read_single_item(table_name, key, projection_expression)

        if response:
            if scope_id:      
                return list(response["scopes"][scope_id]["milestones"].values()), http_status_code
            else:
                scopes = []
                for key, val in response["scopes"].items():
                    scopes.extend(val["milestones"].values())
                return scopes, http_status_code
        else:
            return [], 200

    @exception_handler
    def update_existing_milestone(self, token, customer_id: str, project_id: str, milestones: list):
        """
            Updates an existing milestone.

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                     unique project ID

                milestones: list [required]
                    list object containing milestones to update on DynamoDB

             Returns:
             --------
                response: str
                    dict object containing project information

                http_status_code: int
                    http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # TODO: make table name environment variable
        table_name = f"Projects-{customer_id}"  

        # Key
        key = {"projectId": project_id, "customerId": customer_id}

        # Check if customer and project exist
        logger.info(f"Checking if project ID or organization ID exists: {key}")
        response, http_status_code =  self._db.read_single_item(table_name, key, "projectId")

        success, fail = [], []
        for item in milestones:
            
            scope_id = item["scopeId"]
            milestone_id = item["milestoneId"]

            # Query item from DynamoDB
            projection_expression = f"scopes.{scope_id}.milestones.{milestone_id}"
            previous_item, _ = self._db.read_single_item(table_name, key, projection_expression)
            if not previous_item:
                continue
            previous_item = previous_item["scopes"][scope_id]["milestones"][milestone_id]

            # DynamoDB expression & update milestone
            logger.info(f"Updating milestone {milestone_id}")
            item["lastUpdate"] = str(date.today())
            update_expression = "SET {}".format(", ".join(f"scopes.{scope_id}.milestones.{milestone_id}.#{k}=:{k}" for k in item.keys()))
            expression_attribute_names = {f"#{k}": k for k in item.keys()}
            expression_attribute_values = {f":{k}": v for k, v in item.items()}
            response, http_status_code = self._db.update_item(table_name, key, update_expression, expression_attribute_names, expression_attribute_values)

            # Log workflow
            message = generate_differences_message(previous_item, item)
            if message:
                workflow = Workflows.update_workflows(token, "Update", message, project_id, milestone_id)
                self._db.create_item(f"Workflows-{customer_id}", workflow)


            if 200 <= http_status_code < 300:
                logger.info(f"Project information updated successfully, {http_status_code}")
                success.append(milestone_id)
            else:
                logger.error(f"{response}, {http_status_code}")
                fail.append(milestone_id)

        # Determine status codes

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
        
if __name__ == "__main__":
    milestones_manager = MilestonesManager()