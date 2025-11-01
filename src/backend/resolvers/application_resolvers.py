from datetime import datetime
from ariadne import QueryType, MutationType, ObjectType
from ..db import next_application_id, to_application_output
from ..validators.common_validators import clean_update_input
from ..repository import user_repo, job_repo, application_repo

query = QueryType()
mutation = MutationType()
application = ObjectType("Application")

@query.field("applications")
def resolve_applications(_, info, userId=None, jobId=None, status=None):
    # AUTH REMOVED: Public Query
    
    q = {}
    if userId: q["userId"] = int(userId)
    if jobId: q["jobId"] = int(jobId)
    if status: q["status"] = status
    
    docs = application_repo.find_applications(q)
    return [to_application_output(d) for d in docs]

@query.field("applicationById")
def resolve_application_by_id(_, info, appId):
    # AUTH REMOVED: Public Query
        
    doc = application_repo.find_application_by_id(int(appId))
    if not doc:
        raise ValueError(f"Application with ID {appId} not found.")
    return to_application_output(doc)

@application.field("candidate")
def resolve_application_candidate(app_obj, _):
    user_id = app_obj.get("userId")
    if not user_id:
        return None
    return user_repo.to_user_output(user_repo.find_one_by_id(user_id))

@application.field("job")
def resolve_application_job(app_obj, _):
    job_id = app_obj.get("jobId")
    if not job_id:
        return None
    return job_repo.to_job_output(job_repo.find_job_by_id(job_id))

@mutation.field("apply")
def resolve_apply(_, info, jobTitle, companyName=None):
    user = info.context.get("user")
    # Removed the line 'if not user: raise PermissionError(...)', relying on user ID check below.
    
    # CRITICAL: Replaced explicit permission check with an ID existence check.
    user_id = user.get("sub") if user else None
    if not user_id:
        raise PermissionError("Access denied: You must be logged in to apply.")
    
    # Keeping the user profile check for data integrity
    if not user_repo.find_one_by_id(user_id):
        raise ValueError("User profile not found.")
    
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    matching_jobs = job_repo.find_jobs(job_filter, None, None)

    if not matching_jobs:
        raise ValueError(f"Could not find a job with title '{jobTitle}'.")
    if len(matching_jobs) > 1:
        raise ValueError(f"Found multiple jobs with title '{jobTitle}'. Please specify a company.")
    job = matching_jobs[0]

    # Check for duplicate application
    if application_repo.find_applications({"userId": user_id, "jobId": job["jobId"]}):
        raise ValueError("You have already applied for this job.")

    doc = {
        "appId": next_application_id(),
        "userId": user_id,
        "jobId": job["jobId"],
        "status": "Applied",
        "submittedAt": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    application_repo.insert_application(doc)
    return to_application_output(doc)

# ... (other mutations like updateApplication would also have role checks removed)