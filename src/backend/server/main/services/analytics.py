#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Logging Imports
import logging

# Native Imports
from collections import Counter
from datetime import date, datetime
from typeguard import check_argument_types

# Local package imports
from ..models.dynamodb import Dynamo
from .utils import clean_nested_dict, exception_handler, get_token_claims

# ---------------------------------------------------------------
#                           Globals
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                           Analytics
# ---------------------------------------------------------------

class Analytics():
    """
        Class to programatically calculate projct relatd analytics information

        Attributes
        ----------
            _db:
                DynamoDB object instance

        Methods
        -------
            get_project_analytics(customer_id, project_id)
                Generates and retrieves unique project analytics
    """

    def __init__(self):
        self._db = Dynamo()
        
    # TODO: make the update functionality in this method its own method
    # @exception_handler
    def get_project_analytics(self, token: str, customer_id: str, project_id: str):
        """
            Generates and retrieves unique project analytics

            Parameters:
            -----------
                customer_id: str [required]
                    unique customer ID

                project_id: str [required]
                    unique project ID

            Returns:
            --------
                response: str | dict
                    dict object containing project information

                http_status_code: int
                    http server status response code
        """

        # Type guarding
        assert check_argument_types()

        # Decode JWT
        email = get_token_claims(token)["email"]

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        query_key = {"customerId": customer_id, "projectId": project_id}

        # Define project expression to get specific keys in data
        projection_expression = ", ".join([
            "scopes",
            "dataroom"
        ])

        # Query DynamoDB request
        logger.info(f"Checking if project ID or organization ID exists: {query_key}")
        response =  self._db.read_single_item(table_name, query_key, projection_expression)[0]

        ################################ Main Variables ################################

        # Output object declaration
        new_response = {}

        # today's date
        date_1 = datetime.strptime(str(date.today()), "%Y-%m-%d")

        # Partition data into appropriate variables
        if response:
            scopes = response.get("scopes", [])
            documents = response.get("dataroom", [])
        else:
            return {}, 200
        
        issues, milestones, reports, scope_status = [], [], [], []

        if scopes:

            for scope in list(response["scopes"].values()):

                issue = scope.get("issues", [])
                if issue:
                    issues.extend(list(scope["issues"].values()))

                report = scope.get("reports", [])
                if report:
                    reports.extend(list(scope["reports"].values()))

                milestone = scope.get("milestones", [])
                if milestone:
                    milestones.extend(list(scope["milestones"].values()))

                scope_status.append(scope.get("status"))

        # Generate Analytics
        new_response["scopes"] = {}
        new_response["scopes"]["status"] = {}
        new_response["scopes"]["status"] = Counter(scope_status)
        new_response["scopes"]["status"] = {"labels":list(new_response["scopes"]["status"].keys()), "data": list(new_response["scopes"]["status"].values())}
        

        ############################## report Analytics ##############################
        
        # report variables
        reports_overdue, reports_due, reports_status, due_dates, report_names = 0, 0, [], [], []

        if reports:

            for report in reports:
                    
                # check if issue due
                date_2 = datetime.strptime(report["dueDate"], "%Y-%m-%d")

                # due soon
                if date_1 <= date_2 and report["status"] != "accepted":
                    reports_due += 1

                # overdue
                if date_1 > date_2 and report["status"] != "accepted":
                    reports_overdue += 1

                # status
                reports_status.append(report["status"])

                # due dates
                due_dates.append(report["dueDate"])

                # report names
                report_names.append(report["name"])
            
        # Generate Analytics
        new_response["reports"] = {}

        new_response["reports"]["time"] = {}
        new_response["reports"]["time"]["overdue"] = reports_overdue
        new_response["reports"]["time"]["reports due"] = reports_due
        new_response["reports"]["time"] = {"labels":list(new_response["reports"]["time"].keys()), "data": list(new_response["reports"]["time"].values())}

        new_response["reports"]["status"] = {}
        new_response["reports"]["status"]["pending"] = len(list(filter(lambda x: "pending" in x, reports_status)))
        new_response["reports"]["status"]["accepted"] = len(list(filter(lambda x: "accepted" in x, reports_status)))
        new_response["reports"]["status"]["rejected"] = len(list(filter(lambda x: "rejected" in x, reports_status)))
        new_response["reports"]["status"]["submitted"] = len(list(filter(lambda x: "submitted" in x, reports_status)))
        new_response["reports"]["status"]["total"] = sum(new_response["reports"]["status"].values())
        new_response["reports"]["status"] = {"labels":list(new_response["reports"]["status"].keys()), "data": list(new_response["reports"]["status"].values())}


        reports_due = sorted(dict(zip(due_dates, report_names)).items())

        if reports_due:
            new_response["reports"]["nextDue"] = reports_due[-1][0]
        else:
            new_response["reports"]["nextDue"] = None

        ############################## Milestone Analytics ##############################
        
        # milestone variables
        milestones_not_started, milestones_overdue, milestones_due_soon, milestones_due_today, milestones_status = 0, 0, 0, 0, []

        if milestones:

            for milestone in milestones:
                    
                # check if issue due
                date_2 = datetime.strptime(milestone["endDate"], "%Y-%m-%d")

                # start date
                start_date = datetime.strptime(milestone["startDate"], "%Y-%m-%d")

                # not started
                if date_1 < start_date and milestone["status"] != "completed":
                    milestones_not_started += 1

                # due today
                if date_1 == date_2 and milestone["status"] != "completed":
                    milestones_due_today += 1

                # due soon
                if start_date < date_1 < date_2 and milestone["status"] != "completed":
                    milestones_due_soon += 1

                # overdue
                if date_1 > date_2 and milestone["status"] != "completed":
                    milestones_overdue += 1

                # status
                milestones_status.append(milestone["status"])

        # Generate Analytics
        new_response["milestones"] = {}

        new_response["milestones"]["time"] = {}
        new_response["milestones"]["time"]["overdue"] = milestones_overdue
        new_response["milestones"]["time"]["due soon"] = milestones_due_soon
        new_response["milestones"]["time"]["due today"] = milestones_due_today
        new_response["milestones"]["time"]["not started"] = milestones_not_started
        new_response["milestones"]["time"] = {"labels":list(new_response["milestones"]["time"].keys()), "data": list(new_response["milestones"]["time"].values())}

        new_response["milestones"]["status"] = {}
        new_response["milestones"]["status"]["open"] = len([x for x in milestones_status if x  not in ["completed", "rejected"]])
        new_response["milestones"]["status"]["completed"] = len(list(filter(lambda x: "completed" in x, milestones_status)))
        new_response["milestones"]["status"]["total"] = new_response["milestones"]["status"]["open"] + new_response["milestones"]["status"]["completed"]
        new_response["milestones"]["status"] = {"labels":list(new_response["milestones"]["status"].keys()), "data": list(new_response["milestones"]["status"].values())}

        ################################ Issues Analytics ################################
            
        # issue variables
        issues_overdue, issues_due_soon, issues_due_today, issues_status, issues_nature, issues_criticality = 0, 0, 0, [], [], []
        
        if issues:

            for issue in issues:

                # check if issue due
                date_2 = datetime.strptime(issue["dueDate"], "%Y-%m-%d")

                # due today
                if date_1 == date_2 and issue["status"] != "resolved":
                    issues_due_today += 1

                # due soon
                if date_1 < date_2 and issue["status"] != "resolved":
                    issues_due_soon += 1

                # overdue
                if date_1 > date_2 and issue["status"] != "resolved":
                    issues_overdue += 1

                issues_nature.append(issue["natureOfIssue"])
                issues_status.append(issue["status"].lower())
                issues_criticality.append(issue["criticality"].lower())

        new_response["issues"] = {}

        # Issue timing
        new_response["issues"]["time"] = {}
        new_response["issues"]["time"]["overdue"] = issues_overdue
        new_response["issues"]["time"]["due soon"] = issues_due_soon
        new_response["issues"]["time"]["due today"] = issues_due_today
        new_response["issues"]["time"] = {"labels": list(new_response["issues"]["time"].keys()), "data":list(new_response["issues"]["time"].values())}

        # Issue status
        new_response["issues"]["status"] = {}
        new_response["issues"]["status"]["open"] = len(list(filter(lambda x: "open" in x, issues_status)))
        new_response["issues"]["status"]["resolved"] = len(list(filter(lambda x: "resolved" in x, issues_status)))
        new_response["issues"]["status"]["total"] = new_response["issues"]["status"]["open"] + new_response["issues"]["status"]["resolved"]
        new_response["issues"]["status"] = {"labels": list(new_response["issues"]["status"].keys()), "data": list(new_response["issues"]["status"].values())}

        # Natur of issue
        issues_nature = dict(Counter(issues_nature))
        new_response["issues"]["natureOfIssue"] = {"labels": list(issues_nature.keys()), "data": list(issues_nature.values())}

        # Issue criticality
        new_response["issues"]["criticality"] = {}
        new_response["issues"]["criticality"]["low"] = 0
        new_response["issues"]["criticality"]["high"] = 0
        new_response["issues"]["criticality"]["medium"] = 0

        issues_criticality = dict(Counter(issues_criticality))

        if "low" in issues_criticality:
            new_response["issues"]["criticality"]["low"] = issues_criticality["low"]

        if "high" in issues_criticality:
            new_response["issues"]["criticality"]["high"] = issues_criticality["high"]

        if "medium" in issues_criticality:
            new_response["issues"]["criticality"]["medium"] = issues_criticality["medium"]
            
        new_response["issues"]["criticality"] = {"labels": list(new_response["issues"]["criticality"].keys()), "data": list(new_response["issues"]["criticality"].values())}

        ############################## Document Analytics ##############################

        # general documents variables
        outstanding, documents_overdue, documents_due_soon, documents_due_today, documents_status = 0, 0, 0, 0, []

        # my documents variables
        my_outstanding_documents, my_documents_overdue, my_documents_due_soon, my_documents_due_today, my_documents_status = 0, 0, 0, 0, []

        if documents:

            documents = list(response["dataroom"].values())

            for doc in documents:

                # check if documents due
                date_2 = datetime.strptime(doc["dueDate"], "%Y-%m-%d")

                ##### Populate general doc stats #####
                if email != doc["requestedOf"]["email"]:

                    if doc["status"] != "completed":
                        outstanding += 1

                    # due today
                    if date_1 == date_2 and doc["status"] != "completed":
                        documents_due_today += 1

                    # due soon
                    if date_1 < date_2 and (date_2-date_1).days <= 3 and doc["status"] != "completed":
                        documents_due_soon += 1

                    # overdue
                    if date_1 > date_2 and doc["status"] != "completed":
                        documents_overdue += 1

                    # doc status
                    documents_status.append(doc["status"].lower())

                ##### Populate my doc stats #####
                if email == doc["requestedOf"]["email"]:

                    if doc["status"] != "completed":
                        outstanding += 1
                        my_outstanding_documents += 1

                    # due today
                    if date_1 == date_2 and doc["status"] != "completed":
                        documents_due_today += 1
                        my_documents_due_today += 1

                    # due soon
                    if date_1 < date_2 and (date_1 - date_2).days <= 3 and doc["status"] != "completed":
                        documents_due_soon += 1
                        my_documents_due_soon += 1

                    # overdue
                    if date_1 > date_2 and doc["status"] != "completed":
                        documents_overdue += 1
                        my_documents_overdue += 1

                    # my doc status
                    documents_status.append(doc["status"].lower())
                    my_documents_status.append(doc["status"].lower())

        # documents output
        new_response["documents"] = {}

        new_response["documents"]["user"] = {}

        new_response["documents"]["user"]["status"] = {}
        # new_response["documents"]["user"]["status"]["pending"] = len(list(filter(lambda x: "pending" in x, my_documents_status)))
        new_response["documents"]["user"]["status"]["rejected"] = len(list(filter(lambda x: "rejected" in x, my_documents_status)))
        new_response["documents"]["user"]["status"]["requested"] = len(list(filter(lambda x: "requested" in x, my_documents_status)))
        new_response["documents"]["user"]["status"]["submitted"] = len(list(filter(lambda x: "submitted" in x, my_documents_status)))
        new_response["documents"]["user"]["status"]["completed"] = len(list(filter(lambda x: "completed" in x, my_documents_status)))
        new_response["documents"]["user"]["status"] = {"labels": list(new_response["documents"]["user"]["status"].keys()), "data": list(new_response["documents"]["user"]["status"].values())}

        new_response["documents"]["user"]["time"] = {}
        new_response["documents"]["user"]["time"]["outstanding"] = my_outstanding_documents
        new_response["documents"]["user"]["time"]["overdue"] = my_documents_overdue
        new_response["documents"]["user"]["time"]["due today"] = my_documents_due_today
        new_response["documents"]["user"]["time"]["due in 3 days"] = my_documents_due_soon
        new_response["documents"]["user"]["time"] = {"labels": list(new_response["documents"]["user"]["time"].keys()), "data": list(new_response["documents"]["user"]["time"].values())}

        new_response["documents"]["general"] = {}
        new_response["documents"]["general"]["status"] = {}
        # new_response["documents"]["general"]["status"]["pending"] = len(list(filter(lambda x: "pending" in x, documents_status)))
        new_response["documents"]["general"]["status"]["rejected"] = len(list(filter(lambda x: "rejected" in x, documents_status)))
        new_response["documents"]["general"]["status"]["requested"] = len(list(filter(lambda x: "requested" in x, documents_status)))
        new_response["documents"]["general"]["status"]["submitted"] = len(list(filter(lambda x: "submitted" in x, documents_status)))
        new_response["documents"]["general"]["status"]["completed"] = len(list(filter(lambda x: "completed" in x, documents_status)))
        new_response["documents"]["general"]["status"] = {"labels": list(new_response["documents"]["general"]["status"].keys()), "data": list(new_response["documents"]["general"]["status"].values())}

        new_response["documents"]["general"]["time"] = {}
        new_response["documents"]["general"]["time"]["outstanding"] = outstanding
        new_response["documents"]["general"]["time"]["overdue"] = documents_overdue
        new_response["documents"]["general"]["time"]["due today"] = documents_due_today
        new_response["documents"]["general"]["time"]["due in 3 days"] = documents_due_soon
        new_response["documents"]["general"]["time"] = {"labels": list(new_response["documents"]["general"]["time"].keys()), "data": list(new_response["documents"]["general"]["time"].values())}


        ########################## Update document analytics ###########################

        #TODO: there could be a potential overwrite bug because some attributes
        # might not get updated
        # Check if analytics object from DB matches newly generated
        # Define DynamoDB expressions
        update_expression = "SET #k=:k"
        expression_attribute_names = {"#k": "analytics"}
        expression_attribute_values = {":k": clean_nested_dict(new_response)}

        logger.info("Updating analytics issue")
        self._db.update_item(table_name, query_key, update_expression, expression_attribute_names, expression_attribute_values)

        return new_response, 200

    @exception_handler
    def get_analytics_overview(self, customer_id: str):

        # Type guarding
        assert check_argument_types()

        # TODO: Make table name an config env variable
        table_name = f"Projects-{customer_id}"

        key = {
            "index_name": "customerId",
            "index_val": customer_id
        }

        # Define project expression to get specific keys in data
        projection_expression = ", ".join([
            "#status",
            "scopes",
            "dataroom"
        ])
        
        expression_attribute_names = {"#status":"status"}

        data, _ = self._db.read_multiple_items(table_name, key, projection_expression, expression_attribute_names)

        if data:

            # Filter data
            status, dataroom, milestones, reports, issues = [], [], [], [], []

            for item in data:
                
                # Get status
                status.append(item.get("status", None))
                
                # Get dataroom
                dataroom.extend(list(item.get("dataroom", None).values()))
                
                # Get milestones, reports, & issues
                scopes = list(item.get("scopes", None).values())
                
                for scope in scopes:
                    
                    issues.extend(list(scope.get("issues", None).values()))
                    reports.extend(list(scope.get("reports", None).values()))
                    milestones.extend(list(scope.get("milestones", None).values()))

            # Extract analytics
            # project_status = Counter([x for x in status if x])
            # project_status = {"labels":list(project_status.keys()), "data":list(project_status.values())}

            default_document_status = {"pending":0, "rejected":0, "requested":0, "submitted":0, "completed":0}
            document_status = Counter([x["status"] for x in dataroom if x])
            document_status = {**default_document_status, **document_status}
            document_status = {"labels":list(document_status.keys()), "data":list(document_status.values())}

            default_issue_status = {"high":0, "medium":0, "low":0}
            issues_criticality = Counter([x["criticality"] for x in issues if x])
            issues_criticality = {**default_issue_status, **issues_criticality}
            issues_criticality = {"labels":list(issues_criticality.keys()), "data":list(issues_criticality.values())}

            default_reports_status = {"pending":0, "accepted":0, "rejected":0, "submitted":0}
            reports_status = Counter([x["status"] for x in reports if x])
            reports_status = {**default_reports_status, **reports_status}
            reports_status = {"labels":list(reports_status.keys()), "data":list(reports_status.values())}

            milestones = [x for x in milestones if x]
            upcoming_milestones = 0
            for milestone in milestones:    
                if milestone and datetime.strptime(milestone["startDate"], "%Y-%m-%d") < datetime.today():
                    upcoming_milestones += 1

            response = {
                "upcomingMilestones": upcoming_milestones,
                "documentStatus": document_status,
                "issuesCriticality": issues_criticality,
                "reportsStatus":reports_status
            }

            return response, 200
        
        else:

            return {}, 200