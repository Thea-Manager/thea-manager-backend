#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# Native imports
import logging
from re import sub


# Flask imports
from flask import (
    Blueprint,
    request,
    jsonify, 
    make_response
)

from flask import current_app as app

# local package imports
from main.services import (
    Workflows,
    Analytics,
    UserManager,
    ScopeManager, 
    IssuesTracker,
    ReportsManager,
    DocumentManager,
    ProjectsManager,
    MilestonesManager,
    DiscussionsManager)

from main.services.utils import validate_token

# ---------------------------------------------------------------
#          Class instantiations & Configurations
# ---------------------------------------------------------------

# Service objects instatiations
analytics = Analytics()
user_manager = UserManager()
worfklow_manager = Workflows()
scope_manager = ScopeManager()
issues_tracker = IssuesTracker()
reports_manager = ReportsManager()
projects_manager = ProjectsManager()
documents_manager = DocumentManager()
milestones_manager = MilestonesManager()
discussions_manager = DiscussionsManager()

# Blueprint Configuration
api = Blueprint("", __name__)

# General Configuration
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
#                   Decorators
# ---------------------------------------------------------------

# def verify_access_token(f):

#     (f)
#     def decorated(*args, **kwargs):

#         # Request body
#         logger.info("Get access token")
#         access_token = request.headers["Authorization"]

#         # Token validation
#         logger.info("Validate access token")

#         try:
#             response, code = validate_token(access_token)
#         except Exception as e:
#             return make_response(jsonify({"data": str(e)}), 500)
#         else:
#             if response != "Authorized":

#                 # Return server response to client
#                 return make_response(jsonify({"data": response}), code)

#         return f(*args, **kwargs)

#     return decorated

# ---------------------------------------------------------------
#                   Error handling and Test
# ---------------------------------------------------------------


@api.errorhandler(KeyError)
def general_exceptions(error):
    logger.error(error)
    if "HTTP_" in str(error):
        return make_response(jsonify({"data": f"Missing {sub('HTTP_', '', str(error))} header"}), 500)

@api.errorhandler(400)
def bad_request(error):
    logger.error("Bad request")
    return jsonify({"data": "Bad request"})

@api.errorhandler(404)
def not_found(error):
    logger.error("Not found")
    return jsonify({"data": "Not found"})

@api.route("/", methods=["GET"])
def health_check():
    logger.info("Health check")
    return jsonify({"data": "Health Check"})


# ---------------------------------------------------------------
#        Projects Manager
# ---------------------------------------------------------------

@api.route("/projects/<customerId>", methods=["POST"])
# @verify_access_token
def create_project(customerId: str):

    # Request body
    logger.info(f"POST /projects/{customerId}")
    kwargs = {
        "customer_id": customerId,
        "object_id": request.json.get("projectId"),
        "project_name": request.json.get("projectName"),
        "project_type": request.json.get("projectType"),
        "type": request.json.get("type"),
        "business_unit": request.json.get("businessUnit"),
        "overwrite_generate_code": request.json.get("overwriteGeneratedCode"),
        "internal_project_owner": request.json.get("projectOwner"),
        "internal_client_lead": request.json.get("clientLead"),
        "lead_consulting_partner": request.json.get("consultingPartners"),
        "consulting_companies": request.json.get("consultingCompanies"),
        "start_date": request.json.get("startDate"),
        "estimated_end_date": request.json.get("endDate"),
        "budgeted_cost": request.json.get("budgetedCost"),
        "currency": request.json.get("currency"),
        "linked_projects": request.json.get("linkedProjects"),
        "team_members": request.json.get("teamMembers"),
        "token": request.headers["workflow-token"]
    }

    # Create new project
    response, code = projects_manager.create_new_project(**kwargs)

    # Return server response to client
    return make_response(jsonify({"data": response}), code)

@api.route("/projects/<customerId>/<projectId>", methods=["GET"])
# @verify_access_token
def get_project_details(customerId: str, projectId: str):

    # Request body
    logger.info(f"GET /projects/{customerId}/{projectId}")
    kwargs = {"project_id": projectId, "customer_id": customerId}

    # Get project information
    response, code = projects_manager.get_project_information(**kwargs)

    # Return server response to client
    return make_response(jsonify({"data": response}), code)

# TODO: figure out way to set project status to active or completed
@api.route("/projects/<customerId>", methods=["GET"])
# @verify_access_token
def get_projects_overview(customerId: str):

    # Request body
    logger.info(f"GET /projects/{customerId}")
    kwargs = {"customer_id": customerId}
    
    # Get project overview
    response, code = projects_manager.get_project_overview(**kwargs)

    # Return server response to client
    return make_response(jsonify({"data": response}), code)

@api.route("/projects/<customerId>/<projectId>", methods=["PATCH"])
# @verify_access_token
def update_project_details(customerId: str, projectId: str):

    # Request body
    logger.info(f"PATCH /projects/{customerId}/{projectId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId, 
        "item": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    # Update unique project's information
    logger.info(f"Updating project information")
    response, code = projects_manager.update_project_info(**kwargs)

    # Return server response to client
    return make_response(jsonify({"data": response}), code)

@api.route("/projects/members/<customerId>/<projectId>", methods=["PUT"])
# @verify_access_token
def add_project_members(customerId: str, projectId: str):

    # Request body
    logger.info(f"PUT /projects/members/{customerId}/{projectId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId, 
        "team_members": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    # Add team members to project
    response, code = projects_manager.add_members(**kwargs)

    # Return server response to client
    return make_response(jsonify({"data": response}), code)

@api.route("/projects/members/<customerId>/<projectId>", methods=["DELETE"])
# @verify_access_token
def remove_project_members(customerId: str, projectId: str):

    # Request body
    logger.info(f"DELETE /projects/members/{customerId}/{projectId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId, 
        "team_members": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    # Remove team members from project
    response, code = projects_manager.remove_members(**kwargs)
    
    # Return server response to client
    return make_response(jsonify({"data": response}), code)

# ---------------------------------------------------------------
#        Scopes Manager
# ---------------------------------------------------------------

@api.route("/scopes/<customerId>/<projectId>", methods=["POST"])
# @verify_access_token
def create_scope(customerId: str, projectId: str):

    # Request body
    logger.info(f"POST /scopes/{customerId}/{projectId}")
    kwargs = {
        "project_id": projectId,
        "customer_id": customerId,
        "object_id": request.json.get("scopeId"),
        "scope_name": request.json.get("scopeName"),
        "start_date": request.json.get("startDate"),
        "end_date": request.json.get("endDate"),
        "consultant": request.json.get("consultant"),
        "total_fees": request.json.get("totalFees"),
        "billing_schedule":request.json.get("billingSchedule"),
        "engagement_letter_ref": request.json.get("engagementLetterRef"),
        "team_members": request.json.get("teamMembers"),
        "token": request.headers["workflow-token"]
    }

    # Create new scope
    response, code = scope_manager.create_new_scope(**kwargs)

    # Return server response to client
    return make_response(jsonify({"data": response}), code)

@api.route("/scopes/<customerId>/<projectId>/<scopeId>", methods=["GET"])
# @verify_access_token
def scope_details(customerId: str, projectId: str, scopeId: str):

    # Request body
    logger.info(f"GET /scopes/<customerId>/{projectId}/{scopeId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId, 
        "scope_id": scopeId
    }

    # Get scope details
    response, code = scope_manager.get_scope_details(**kwargs)
    
    # Return server response to client
    return make_response(jsonify({"data": response}), code)

@api.route("/scopes/<customerId>/<projectId>", methods=["GET"])
# @verify_access_token
def scopes_overview(customerId: str, projectId: str):
  
    # Request body
    logger.info("GET /scopes/{customerId}/{projectId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId
    }

    response, code = scope_manager.get_scopes_overview(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/scopes/members/<customerId>/<projectId>/<scopeId>", methods=["PUT"])
# @verify_access_token
def add_scope_members(customerId: str, projectId: str, scopeId: str):

    # Request body
    logger.info(f"PUT /scopes/members/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "project_id": projectId,
        "customer_id": customerId, 
        "scope_id": scopeId, 
        "team_members": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    # Add new scope member
    response, code = scope_manager.add_scope_members(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/scopes/members/<customerId>/<projectId>/<scopeId>", methods=["DELETE"])
# @verify_access_token
def remove_scope_members(customerId: str, projectId: str, scopeId: str):

    # Request body
    logger.info(f"DELETE /scopes/members/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId, 
        "scope_id": scopeId, 
        "team_members": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    # Remove scope member
    response, code = scope_manager.remove_scope_members(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/scopes/<customerId>/<projectId>", methods=["PATCH"])
# @verify_access_token
def update_scope(customerId: str, projectId: str):
    
    # Request Body
    logger.info(f"PATCH /scopes/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "items": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    response, code = scope_manager.update_scope_details(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/scopes/<customerId>/<projectId>", methods=["DELETE"])
# @verify_access_token
def delete_scope(customerId: str, projectId: str):
   
    # Request body
    logger.info(f"DELETE /scopes/{customerId}/{projectId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId, 
        "scopes": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    response, code = scope_manager.delete_scope(**kwargs)
    return make_response(jsonify({"data": response}), code)

# ---------------------------------------------------------------
#        Milestones Manager
# ---------------------------------------------------------------

@api.route("/milestones/<customerId>/<projectId>/<scopeId>", methods=["POST"])
# @verify_access_token
def create_milestone(customerId: str, projectId: str, scopeId: str):

    # Request body
    logger.info(f"POST /milestones/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "customer_id": customerId,
        "project_id":projectId,
        "scope_id": scopeId,
        "object_id": request.json.get("milestoneId"),
        "milestone_name": request.json.get("milestoneName"),
        "start_date": request.json.get("startDate"),
        "end_date": request.json.get("endDate"),
        "phase": request.json.get("phase"),
        "assignee": request.json.get("assignee"),
        "invoiceable": request.json.get("invoiceable"),
        "cost": request.json.get("cost"),
        "currency": request.json.get("currency"),
        "business_unit": request.json.get("businessUnit"),
        "notes":request.json.get("notes"),
        "token": request.headers["workflow-token"]
    }

    response, code = milestones_manager.create_new_milestone(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/milestones/<customerId>/<projectId>/<scopeId>/<milestoneId>", methods=["GET"])
# @verify_access_token
def milestone_details(customerId: str, projectId: str, scopeId: str, milestoneId: str):

    # Request body
    logger.info(f"GET /milestones/{customerId}/{projectId}/{scopeId}/{milestoneId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "scope_id": scopeId, 
        "milestone_id": milestoneId
    }

    response, code = milestones_manager.get_milestone_details(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/milestones/<customerId>/<projectId>", methods=["GET"])
@api.route("/milestones/<customerId>/<projectId>/<scopeId>", methods=["GET"])
# @verify_access_token
def milestones_overview(customerId: str, projectId: str, scopeId: str = ""):
    
    # Request body
    logger.info(f"GET /milestones/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "scope_id": scopeId
    }

    response, code = milestones_manager.get_milestones_overview(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/milestones/<customerId>/<projectId>", methods=["PATCH"])
# @verify_access_token
def update_milestone(customerId: str, projectId: str):

    # Request Body
    logger.info(f"PATCH /milestones/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "milestones": request.get_json(), 
        "token": request.headers["workflow-token"]
    }
 
    response, code = milestones_manager.update_existing_milestone(**kwargs)
    return make_response(jsonify({"data": response}), code)

# @api.route("/milestones/<customerId>/<projectId>/<scopeId>/<milestoneId>", methods=["DELETE"])
# # @verify_access_token
# def delete_milestone(customerId: str, projectId: str, scopeId: str, milestoneId: str):
    
#     # Request Body
#     logger.info(f"DELETE /milestones/{customerId}/{projectId}/{scopeId}/{milestoneId}")
#     kwargs = {
#         "customer_id": customerId, 
#         "project_id": projectId, 
#         "scope_id": scopeId, 
#         "milestone_id": milestoneId
#     }

# ---------------------------------------------------------------
#        Issues Tracker
# ---------------------------------------------------------------

@api.route("/issues/<customerId>/<projectId>/<scopeId>", methods=["POST"])
# @verify_access_token
def create_issue(customerId: str, projectId: str, scopeId: str):

    # Request body
    logger.info(f"POST /issues/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "customer_id":customerId,
        "project_id":projectId,
        "scope_id": scopeId,
        "object_id": request.json.get("issueId"),
        "issue_name":request.json.get("issueName"),
        "region":request.json.get("region"),
        "business_unit":request.json.get("businessUnit"),
        "due_date":request.json.get("dueDate"),
        "date_of_raise":request.json.get("dateOfRaise"),
        "nature_of_issue":request.json.get("natureOfIssue"),
        "criticality":request.json.get("criticality"),
        "issue_description":request.json.get("issueDescription"),
        "impact_value":request.json.get("impactValue"),
        "currency":request.json.get("currency"),
        "impact_on":request.json.get("impactOn"),
        "document_ref":request.json.get("documentRef"),
        "issue_owner":request.json.get("issueOwner"),
        "resolution_path":request.json.get("resolutionPath"),
        "token": request.headers["workflow-token"]    
    }

    response, code = issues_tracker.create_new_issue(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/issues/<customerId>/<projectId>/<scopeId>/<issuesId>", methods=["GET"])
# @verify_access_token
def issue_details(customerId: str, projectId: str, scopeId: str, issuesId: str):

    # Request Body
    logger.info("GET /issues/{customerId}/{projectId}/{scopeId}/{issuesId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "scope_id": scopeId, 
        "issues_id": issuesId
    }

    response, code = issues_tracker.get_issue_details(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/issues/<customerId>/<projectId>", methods=["GET"])
@api.route("/issues/<customerId>/<projectId>/<scopeId>", methods=["GET"])
# @verify_access_token
def issues_overview(customerId: str, projectId: str, scopeId: str = ""):
   
    # Request Body
    logger.info("GET /issues/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "scope_id": scopeId
    }

    response, code = issues_tracker.get_issues_overview(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/issues/<customerId>/<projectId>", methods=["PATCH"])
# @verify_access_token
def update_issue(customerId: str, projectId: str):

    # Request Body
    logger.info(f"PATCH /issues/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "items": request.get_json(), 
        "token":request.headers["workflow-token"]
    }

    response, code = issues_tracker.update_existing_issue(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/issues/<customerId>/<projectId>/<scopeId>", methods=["DELETE"])
# @verify_access_token
def delete_issue(customerId: str, projectId: str, scopeId: str):
    
    # Request Body
    logger.info(f"DELETE /issues/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "scope_id": scopeId, 
        "issues": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    response, code = issues_tracker.delete_existing_issues(**kwargs)
    return make_response(jsonify({"data": response}), code)

# ---------------------------------------------------------------
#                           Reports
# ---------------------------------------------------------------

@api.route("/reports/<customerId>/<projectId>/<scopeId>", methods=["POST"])
# @verify_access_token
def create_report(customerId: str, projectId: str, scopeId: str):

    # Request body
    logger.info(f"POST /issues/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "project_id": projectId,
        "customer_id": customerId,
        "scope_id": scopeId,
        "object_id": request.json.get("reportId"),
        "name": request.json.get("name"),
        "due_date": request.json.get("dueDate"),
        "requested_by": request.json.get("requestedBy"),
        "submitted_by": request.json.get("submittedBy"),
        "description": request.json.get("description"),
        "token": request.headers["workflow-token"]
    }

    response, code = reports_manager.create_scope_report(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/reports/<customerId>/<projectId>/<scopeId>/<reportId>", methods=["GET"])
# @verify_access_token
def report_details(customerId: str, projectId: str, scopeId: str, reportId: str):

    # Request body
    logger.info(f"GET /reports/{customerId}/{projectId}/{scopeId}/{reportId}")
    kwargs = {
        "project_id": projectId,
        "customer_id": customerId,
        "report_id": reportId,
        "scope_id": scopeId
    }

    response, code = reports_manager.get_report_information(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/reports/<customerId>/<projectId>", methods=["GET"])
@api.route("/reports/<customerId>/<projectId>/<scopeId>", methods=["GET"])
# @verify_access_token
def reports_overview(customerId: str, projectId: str, scopeId: str = ""):

    # Request body
    logger.info(f"GET /reports/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "project_id": projectId, 
        "customer_id": customerId, 
        "scope_id": scopeId
    }

    response, code = reports_manager.get_reports_overview(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/reports/<customerId>/<projectId>", methods=["PATCH"])
# @verify_access_token
def update_report(customerId: str, projectId: str):

    # Request Body
    logger.info(f"PATCH /reports/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "items": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    response, code = reports_manager.update_existing_reports(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/reports/<customerId>/<projectId>/<scopeId>", methods=["DELETE"])
# @verify_access_token
def delete_report(customerId: str, projectId: str, scopeId: str):
    
    # Request Body
    logger.info(f"DELETE /milestones/{customerId}/{projectId}/{scopeId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId,
        "scope_id": scopeId,
        "reports": request.get_json()
    }

    response, code = reports_manager.delete_existing_reports(**kwargs)
    return make_response(jsonify({"data": response}), code)

# ---------------------------------------------------------------
#                           Analytics
# ---------------------------------------------------------------

@api.route("/analytics/<customerId>", methods=["GET"])
# @verify_access_token
def overview_analytics(customerId: str):
    
    # Request body
    logger.info(f"GET /analytics/{customerId}")
    kwargs = {"customer_id": customerId}

    response, code = analytics.get_analytics_overview(**kwargs)
    return make_response(jsonify({"data": response}), code) 


@api.route("/analytics/<customerId>/<projectId>", methods=["GET"])
# @verify_access_token
def project_analytics(customerId: str, projectId: str):
   
    # Request body
    logger.info(f"GET /analytics/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId,
        "token": request.headers["workflow-token"]
    }

    response, code = analytics.get_project_analytics(**kwargs)
    return make_response(jsonify({"data": response}), code)


# ---------------------------------------------------------------
#                       Document Manager
# ---------------------------------------------------------------

@api.route("/dataroom/<customerId>/<projectId>", methods=["POST"])
# @verify_access_token
def create_document_request(customerId: str, projectId: str):
    
    # Request body
    logger.info(f"POST /dataroom/request/{customerId}/{projectId}")
    kwargs = {
        "project_id": projectId,
        "customer_id": customerId,
        "object_id": request.json.get("docReqId"),
        "requested_of": request.json.get("requestedOf"),
        "requested_by": request.json.get("requestedBy"),
        "name": request.json.get("name"),
        "due_date": request.json.get("dueDate"),
        "description": request.json.get("description"),
        "token": request.headers["workflow-token"]
    }

    response, code = documents_manager.document_request(**kwargs)
    return make_response(jsonify({"data": response}), code) 

@api.route("/dataroom/requests/<customerId>/<projectId>", methods=["GET"])
@api.route("/dataroom/requests/<customerId>/<projectId>/<docReqId>", methods=["GET"])
# @verify_access_token
def get_document_requests(customerId: str, projectId: str, docReqId: str = ""):
    # Request body
    logger.info(f"POST /dataroom/request/{customerId}/{projectId}/{docReqId}")
    kwargs = {
        "project_id": projectId,
        "customer_id": customerId,
        "doc_req_id": docReqId
    }

    response, code = documents_manager.document_request_overview(**kwargs)
    return make_response(jsonify({"data": response}), code) 

@api.route("/dataroom/<customerId>/<projectId>", methods=["PATCH"])
# @verify_access_token
def update_document_requests(customerId: str, projectId: str):

    # Request Body
    logger.info(f"PATCH /reports/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "items": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    response, code = documents_manager.update_request_document_details(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/dataroom/documents/<customerId>/<projectId>", methods=["GET"])
@api.route("/dataroom/documents/<customerId>/<projectId>/<itemId>", methods=["GET"])
# @verify_access_token
def get_documents_overview(customerId: str, projectId: str, itemId: str = ""):

    # Request body
    logger.info(f"GEET /dataroom/{customerId}/{projectId}/{itemId}")
    kwargs = {
        "item_id": itemId,
        "project_id": projectId,
        "customer_id": customerId
    }

    response, code = documents_manager.get_data_room_contents(**kwargs)
    return make_response(jsonify({"data": response}), code)    

@api.route("/dataroom/presigned/<customerId>/<projectId>/<itemId>", methods=["POST"])
# @verify_access_token
def presigned_post(customerId: str, projectId: str, itemId: str):
    
    # Request body
    logger.info(f"POST /dataroom/presigned/{customerId}/{itemId}")
    kwargs = {
        "item_id": itemId,
        "project_id": projectId,
        "customer_id": customerId,
        "metadata": request.json.get("metadata"),
        "filenames": request.json.get("filenames"),
        "token": request.headers["workflow-token"]
    }

    response, code = documents_manager.presigned_url_post(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/dataroom/presigned/<customerId>/<projectId>/<itemId>/<filename>", methods=["GET"])
@api.route("/dataroom/presigned/<customerId>/<projectId>/<itemId>/<filename>/<versionId>", methods=["GET"])
# @verify_access_token
def presigned_get(customerId: str, projectId: str, itemId: str, filename: str, versionId: str = ""):
    
    # Request body
    logger.info(f"GET /dataroom/presigned/{customerId}/{projectId}/{itemId}")
    kwargs = {
        "item_id": itemId,
        "project_id": projectId,
        "customer_id": customerId,
        "filename": filename,
        "version_id": versionId
    }
    response, code = documents_manager.presigned_url_get(**kwargs)
    return make_response(jsonify({"data": response}), code)


# ---------------------------------------------------------------
#                           User Manager
# ---------------------------------------------------------------

@api.route("/users/<organizationId>/<email>", methods=["GET"])
# @verify_access_token
def user_details(organizationId: str, email: str):

    # Request body
    logger.info(f"GET /users/{organizationId}/{email}")
    kwargs = {
        "organization_id": organizationId, 
        "email": email
    }

    # Get user details
    logger.info(f"Get user {email} details")
    response, code = user_manager.get_unique_user(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/users/<organizationId>", methods=["GET"])
# @verify_access_token
def users_overview(organizationId: str):

    # Request body
    logger.info(f"GET /users/{organizationId}")
    kwargs = {"organization_id": organizationId}

    # Get user details
    logger.info(f"Get organization {organizationId} users overview")
    response, code = user_manager.get_user_overview(**kwargs)
    return make_response(jsonify({"data": response}), code)

# ---------------------------------------------------------------
#                          Workflows Manager
# ---------------------------------------------------------------

@api.route("/workflows/<customerId>/<projectId>/<typeId>", methods=["GET"])
# @verify_access_token
def workflow_overview(customerId: str, projectId: str, typeId: str):

    # Request body
    logger.info(f"GET /workflows/{customerId}/{projectId}")
    actions = request.args.get("actions")
    if actions:
        actions = actions.split(",")
    else:
        actions = []

    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId, 
        "actions": actions, 
        "type_id": typeId
    }

    # Get user details
    logger.info(f"Get workflow details")
    response, code = worfklow_manager.get_workflows(**kwargs)
    return make_response(jsonify({"data": response}), code)


# ---------------------------------------------------------------
#                          Chat-records Manager
# ---------------------------------------------------------------

@api.route("/chat-records/<customerId>/<itemId>", methods=["GET"])
# @verify_access_token
def chat_records(customerId: str, itemId: str):

    # Request body
    kwargs = {"item_id": itemId, "customer_id": customerId, "table_name": "ChatRecords"}
    
    # Get previous messages
    response, code = discussions_manager.get_previous_messages(**kwargs)
    response.sort(key=lambda x: x["timestamp"], reverse=False)

    # Return server response
    return make_response(jsonify({"data": response}), code)


# ---------------------------------------------------------------
#                          Discussions Manager
# ---------------------------------------------------------------

@api.route("/discussions/<customerId>/<projectId>", methods=["POST"])
# @verify_access_token
def create_discussions(customerId: str, projectId: str):

    # Request Body
    logger.info(f"POST /discussions/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId,
        "object_id": request.json.get("discussionId"),
        "title": request.json.get("title"), 
        "description": request.json.get("description"),
        "creator": request.json.get("creator"),
        "token": request.headers["workflow-token"]
    }

    # Return server response
    response, code = discussions_manager.create_new_discussions(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/discussions/<customerId>/<projectId>", methods=["PATCH"])
# @verify_access_token
def update_discussions(customerId: str, projectId: str):
    # Request Body
    logger.info(f"PATCH /discussions/{customerId}/{projectId}")
    kwargs = {
        "customer_id": customerId, 
        "project_id": projectId,
        "items": request.get_json(), 
        "token": request.headers["workflow-token"]
    }

    # Return server response
    response, code = discussions_manager.update_discussion_details(**kwargs)
    return make_response(jsonify({"data": response}), code)

@api.route("/discussions/<customerId>/<projectId>", methods=["GET"])
# @verify_access_token
def discussion_details(customerId: str, projectId: str):

    # Request body
    kwargs = {"project_id": projectId, "customer_id": customerId}
    
    # Get previous messages
    response, code = discussions_manager.get_discussion_details(**kwargs)

    # Return server response
    return make_response(jsonify({"data": response}), code)

@api.route("/discussions/messages/<customerId>/<itemId>", methods=["GET"])
# @verify_access_token
def discussion_messages(customerId: str, itemId: str):

    # Request body
    kwargs = {"item_id": itemId, "customer_id": customerId, "table_name": "Discussions"}
    
    # Get previous messages
    response, code = discussions_manager.get_previous_messages(**kwargs)
    response = sorted(response, key = lambda x: x["timestamp"], reverse = False)

    # Return server response
    return make_response(jsonify({"data": response}), code)


# ---------------------------------------------------------------
#                   Script Entrypoint
# ---------------------------------------------------------------

if __name__ == "__main__":
    pass