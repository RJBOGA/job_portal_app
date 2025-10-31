from typing import Optional
from ariadne import QueryType, MutationType
from ..validators.common_validators import require_non_empty_str, validate_date_str, clean_update_input
from ..db import next_user_id
from ..repository.user_repo import (
    to_user_output, build_filter, name_filter_ci, find_users, find_one_by_id,
    insert_user, update_one, update_many, delete_one, delete_many
)

query = QueryType()
mutation = MutationType()

@query.field("users")
def resolve_users(_, info, limit=None, skip=None, FirstName=None, LastName=None, DateOfBirth=None):
    # --- AUTH DISABLED ---
    # user = info.context.get("user")
    # if not user:
    #     raise PermissionError("Access denied: Authentication required.")
    # if user.get("role") not in ["recruiter", "admin"]:
    #     raise PermissionError("Access denied: Only recruiters can list all users.")
        
    if DateOfBirth:
        DateOfBirth = validate_date_str(DateOfBirth)
    q = build_filter(FirstName, LastName, DateOfBirth)
    docs = find_users(q, skip, limit)
    return [to_user_output(d) for d in docs]

@query.field("userById")
def resolve_user_by_id(_, info, UserID):
    doc = find_one_by_id(int(UserID))
    return to_user_output(doc)

@mutation.field("createUser")
def resolve_create_user(*_, input):
    first = require_non_empty_str(input.get("FirstName"), "FirstName")
    last = require_non_empty_str(input.get("LastName"), "LastName")
    dob = validate_date_str(input.get("DateOfBirth"))
    title = (input.get("ProfessionalTitle") or None)
    summary = (input.get("Summary") or None)
    skills = input.get("skills", [])

    doc = {
        "UserID": next_user_id(),
        "FirstName": first,
        "LastName": last,
        "DateOfBirth": dob,
        "ProfessionalTitle": title,
        "Summary": summary,
        "skills": skills,
    }
    insert_user(doc)
    return to_user_output(doc)

@mutation.field("updateUser")
def resolve_update_user(_, info, UserID, input):
    # --- AUTH DISABLED ---
    # user = info.context.get("user")
    # if not user:
    #     raise PermissionError("Access denied: Authentication required.")
    # if user.get("role") != "admin" and user.get("sub") != int(UserID):
    #     raise PermissionError("Access denied: You can only update your own profile.")

    if "FirstName" in input and input["FirstName"] is not None:
        require_non_empty_str(input["FirstName"], "FirstName")
    if "LastName" in input and input["LastName"] is not None:
        require_non_empty_str(input["LastName"], "LastName")
    if "DateOfBirth" in input and input["DateOfBirth"] is not None:
        input["DateOfBirth"] = validate_date_str(input["DateOfBirth"])

    set_fields = clean_update_input(input)
    if not set_fields:
        raise ValueError("No fields provided to update")

    updated = update_one({"UserID": int(UserID)}, set_fields)
    return to_user_output(updated)

@mutation.field("updateMyProfile")
def resolve_update_my_profile(_, info, input):
    # This mutation cannot work without authentication.
    raise NotImplementedError("The 'updateMyProfile' mutation is disabled. Please use 'update user with id <ID> ...' for testing.")

@mutation.field("deleteUser")
def resolve_delete_user(_, info, UserID):
    # --- AUTH DISABLED ---
    # user = info.context.get("user")
    # if not user:
    #     raise PermissionError("Access denied: Authentication required.")
    # if user.get("role") != "admin" and user.get("sub") != int(UserID):
    #     raise PermissionError("Access denied: You can only delete your own profile.")
    
    return delete_one({"UserID": int(UserID)}) == 1

# ... (Deprecated mutations like updateUserByName are unchanged)