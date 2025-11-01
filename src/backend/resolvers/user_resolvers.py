from typing import Optional
from ariadne import QueryType, MutationType
from ..validators.common_validators import require_non_empty_str, validate_date_str, clean_update_input
from ..db import next_user_id
from ..repository.user_repo import (
    to_user_output, build_filter, name_filter_ci, find_users, find_one_by_id,
    insert_user, update_one, delete_one
)

query = QueryType()
mutation = MutationType()

@query.field("users")
def resolve_users(_, info, limit=None, skip=None, FirstName=None, LastName=None, DateOfBirth=None):
    # Public Query
    if DateOfBirth:
        DateOfBirth = validate_date_str(DateOfBirth)
    q = build_filter(FirstName, LastName, DateOfBirth)
    docs = find_users(q, skip, limit)
    return [to_user_output(d) for d in docs]

@query.field("userById")
def resolve_user_by_id(_, info, UserID):
    # Public Query: Anyone can look up a user by ID
    doc = find_one_by_id(int(UserID))
    return to_user_output(doc)

@mutation.field("updateUser")
def resolve_update_user(_, info, UserID, input):
    user = info.context.get("user")
    # CRITICAL: Replaced generic 'if not user' check.
    user_id = user.get("sub") if user else None
    if not user_id:
        raise PermissionError("Access denied: Authentication required.")
    
    if "FirstName" in input and input["FirstName"] is not None:
        require_non_empty_str(input["FirstName"], "FirstName")
    if "LastName" in input and input["LastName"] is not None:
        require_non_empty_str(input["LastName"], "LastName")
    
    set_fields = clean_update_input(input)
    if not set_fields:
        raise ValueError("No fields provided to update")

    updated = update_one({"UserID": int(UserID)}, set_fields)
    return to_user_output(updated)

@mutation.field("updateMyProfile")
def resolve_update_my_profile(_, info, input):
    user = info.context.get("user")
    # FIX: This is the exact line that was throwing the error.
    # Replaced with an explicit check on user_id existence.
    user_id = user.get("sub") if user else None
    if not user_id:
        raise PermissionError("Access denied: You must be logged in to update your profile.")

    if "FirstName" in input and input["FirstName"] is not None:
        require_non_empty_str(input["FirstName"], "FirstName")
    if "LastName" in input and input["LastName"] is not None:
        require_non_empty_str(input["LastName"], "LastName")

    set_fields = clean_update_input(input)
    if not set_fields:
        raise ValueError("No fields were provided to update.")

    updated_doc = update_one({"UserID": int(user_id)}, set_fields)

    if not updated_doc:
        raise ValueError(f"Could not find a user profile for your account (ID: {user_id}). Please contact support.")
        
    return to_user_output(updated_doc)

@mutation.field("deleteUser")
def resolve_delete_user(_, info, UserID):
    user = info.context.get("user")
    # CRITICAL: Replaced generic 'if not user' check.
    user_id = user.get("sub") if user else None
    if not user_id:
        raise PermissionError("Access denied: Authentication required.")
    
    return delete_one({"UserID": int(UserID)}) == 1