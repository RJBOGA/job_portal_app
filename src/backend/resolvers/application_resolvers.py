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
    # --- AUTH DISABLED ---
    q = {}
    if userId:
        q["userId"] = int(userId)
    if jobId:
        q["jobId"] = int(jobId)
    if status:
        q["status"] = status
    docs = application_repo.find_applications(q)
    return [to_application_output(d) for d in docs]

@query.field("applicationById")
def resolve_application_by_id(_, info, appId):
    # --- AUTH DISABLED ---
    doc = application_repo.find_application_by_id(int(appId))
    if not doc:
        raise ValueError(f"Application with ID {appId} not found.")
    return to_application_output(doc)

@application.field("candidate")
def resolve_application_candidate(app_obj, _):
    user_id = app_obj.get("userId")
    if not user_id: return None
    user_doc = user_repo.find_one_by_id(user_id)
    return user_repo.to_user_output(user_doc)

@application.field("job")
def resolve_application_job(app_obj, _):
    job_id = app_obj.get("jobId")
    if not job_id: return None
    job_doc = job_repo.find_job_by_id(job_id)
    return job_repo.to_job_output(job_doc)

@mutation.field("createApplication")
def resolve_create_application(_, info, input):
    # --- AUTH DISABLED ---
    user_id = input.get("userId")
    job_id = input.get("jobId")

    if not user_repo.find_one_by_id(user_id):
        raise ValueError(f"Validation failed: User with ID {user_id} does not exist.")
    if not job_repo.find_job_by_id(job_id):
        raise ValueError(f"Validation failed: Job with ID {job_id} does not exist.")
    if application_repo.find_applications({"userId": user_id, "jobId": job_id}):
        raise ValueError("This user has already applied for this job.")

    doc = {
        "appId": next_application_id(),
        "userId": user_id,
        "jobId": job_id,
        "status": "Applied",
        "submittedAt": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "notes": input.get("notes")
    }
    application_repo.insert_application(doc)
    return to_application_output(doc)

@mutation.field("apply")
def resolve_apply(_, info, jobTitle, companyName=None):
    # This mutation requires a logged-in user and cannot function.
    raise NotImplementedError("The 'apply' mutation is disabled. Please use 'create application for user <ID> and job <ID>' for testing.")

@mutation.field("updateApplication")
def resolve_update_application(_, info, appId, input):
    # --- AUTH DISABLED ---
    existing_app = application_repo.find_application_by_id(int(appId))
    if not existing_app:
        raise ValueError(f"Application with ID {appId} not found.")
    
    set_fields = clean_update_input(input)
    if not set_fields:
        raise ValueError("No fields provided to update.")
        
    updated = application_repo.update_one_application({"appId": int(appId)}, set_fields)
    return to_application_output(updated)