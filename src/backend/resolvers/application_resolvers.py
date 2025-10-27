from datetime import datetime
from ariadne import QueryType, MutationType, ObjectType
from ..db import next_application_id, to_application_output
from ..validators.common_validators import clean_update_input

# Import repositories for all entities, as we need them for lookups
from ..repository import user_repo, job_repo, application_repo

# Create QueryType, MutationType, and a new ObjectType for resolving linked fields
query = QueryType()
mutation = MutationType()
application = ObjectType("Application") # Binds resolver functions to the Application type in the schema

@query.field("applications")
def resolve_applications(*_, userId=None, jobId=None, status=None):
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
def resolve_application_by_id(*_, appId):
    doc = application_repo.find_application_by_id(int(appId))
    if not doc:
        raise ValueError(f"Application with ID {appId} not found.")
    return to_application_output(doc)

# --- Field level resolvers for linked types ---
# When GraphQL asks for the 'candidate' field on an Application, this function runs
@application.field("candidate")
def resolve_application_candidate(app_obj, _):
    user_id = app_obj.get("userId")
    if not user_id:
        return None
    # Use the user_repo to fetch the user data
    user_doc = user_repo.find_one_by_id(user_id)
    return user_repo.to_user_output(user_doc)

# When GraphQL asks for the 'job' field on an Application, this function runs
@application.field("job")
def resolve_application_job(app_obj, _):
    job_id = app_obj.get("jobId")
    if not job_id:
        return None
    # Use the job_repo to fetch the job data
    job_doc = job_repo.find_job_by_id(job_id)
    return job_repo.to_job_output(job_doc)

# --- Mutations ---
@mutation.field("createApplication")
def resolve_create_application(_, info, input):
    user = info.context.get("user")
    if not user or user.get("role") != "user":
        raise PermissionError("Access denied: Only users can submit applications.")

    # Ensure user can only create applications for themselves
    input_user_id = input.get("userId")
    token_user_id = user.get("sub")
    if input_user_id != token_user_id:
        raise PermissionError("Access denied: You can only create applications for yourself.")

    user_id = input.get("userId")
    job_id = input.get("jobId")

    # --- Validation ---
    if not user_repo.find_one_by_id(user_id):
        raise ValueError(f"Validation failed: User with ID {user_id} does not exist.")
    if not job_repo.find_job_by_id(job_id):
        raise ValueError(f"Validation failed: Job with ID {job_id} does not exist.")

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
    user = info.context.get("user")
    if not user or user.get("role") != "user":
        raise PermissionError("Access denied: Only users can apply for jobs.")
    
    user_id = user.get("sub")  # Get user ID from the token's subject
    
    # Check if user profile exists
    user_doc = user_repo.find_one_by_id(user_id)
    if not user_doc:
        raise ValueError("User profile not found. Please complete your profile first.")
    
    # 2. Find the job (this logic remains the same)
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    matching_jobs = job_repo.find_jobs(job_filter, None, None)

    if len(matching_jobs) == 0:
        raise ValueError(f"Could not find a job with title '{jobTitle}' at company '{companyName or ''}'.")
    if len(matching_jobs) > 1:
        raise ValueError(f"Found multiple jobs with title '{jobTitle}'. Please specify a company.")
    job = matching_jobs[0]

    # 3. Create the application using the found IDs
    application_input = {"userId": user["UserID"], "jobId": job["jobId"]}
    return resolve_create_application(None, input=application_input)


@mutation.field("updateApplication")
def resolve_update_application(_, info, appId, input):
    user = info.context.get("user")
    if not user:
        raise PermissionError("Access denied: Authentication required.")

    # Get the application to check ownership/permissions
    existing_app = application_repo.find_application_by_id(int(appId))
    if not existing_app:
        raise ValueError(f"Application with ID {appId} not found.")

    # Users can only update their own applications
    # Recruiters can update any application (e.g. to change status)
    if user.get("role") == "user" and existing_app.get("userId") != user.get("sub"):
        raise PermissionError("Access denied: You can only update your own applications.")
    elif user.get("role") != "user" and user.get("role") != "recruiter":
        raise PermissionError("Access denied: Only users or recruiters can update applications.")

    set_fields = clean_update_input(input)
    if not set_fields:
        raise ValueError("No fields provided to update.")
        
    updated = application_repo.update_one_application({"appId": int(appId)}, set_fields)
    if not updated:
        raise ValueError(f"Application with ID {appId} not found for update.")
    return to_application_output(updated)