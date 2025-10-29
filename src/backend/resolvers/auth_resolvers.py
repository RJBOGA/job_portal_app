from ariadne import MutationType
from graphql import GraphQLError
from ..db import accounts_collection, users_collection, next_user_id
from ..services import auth_service
from datetime import datetime

mutation = MutationType()

@mutation.field("register")
def resolve_register(*_, email, password, role):
    # Validation
    if role not in ["user", "recruiter"]:
        raise GraphQLError("Role must be either 'user' or 'recruiter'.")
    if accounts_collection().find_one({"email": email}):
        raise GraphQLError("User already exists")

    # Create Account
    hashed_password = auth_service.hash_password(password)
    account_id = next_user_id() # We can reuse the user counter for a single ID space
    
    account_doc = {
        "_id": account_id,
        "email": email,
        "password": hashed_password,
        "role": role,
        "createdAt": datetime.utcnow()
    }
    accounts_collection().insert_one(account_doc)

    # If it's a job seeker, create a linked user profile
    if role == "user":
        user_doc = {
            "UserID": account_id,
            "FirstName": "New", # Default values
            "LastName": "User",
            # email could be stored here too for convenience
        }
        users_collection().insert_one(user_doc)
        
    # Create JWT
    token = auth_service.create_token(account_id=account_id, email=email, role=role)
    return {"token": token}

@mutation.field("login")
def resolve_login(*_, email, password):
    account = accounts_collection().find_one({"email": email})
    if not account or not auth_service.check_password(password, account["password"]):
        raise GraphQLError("Invalid email or password.")

    token = auth_service.create_token(
        account_id=account["_id"],
        email=account["email"],
        role=account["role"]
    )
    return {"token": token}