import sys
import os
from datetime import datetime

# Add the project root to the Python path to allow imports from `src`
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Now we can import our backend modules
from src.backend import db
from src.backend.services import auth_service

# --- Sample Data ---

# We'll create two main users for testing: a job seeker and a recruiter
# The password for all sample accounts will be 'password123'

ACCOUNTS_DATA = [
    {"_id": 1, "email": "alice@example.com", "role": "user"},
    {"_id": 2, "email": "bob@example.com", "role": "user"},
    {"_id": 3, "email": "charlie@example.com", "role": "user"},
    {"_id": 101, "email": "recruiter@corp.com", "role": "recruiter"},
]

USERS_DATA = [
    {
        "UserID": 1, "FirstName": "Alice", "LastName": "Johnson", "ProfessionalTitle": "Data Scientist",
        "skills": ["Python", "Pandas", "PyTorch", "SQL", "Machine Learning"]
    },
    {
        "UserID": 2, "FirstName": "Bob", "LastName": "Williams", "ProfessionalTitle": "Frontend Developer",
        "skills": ["JavaScript", "React", "TypeScript", "CSS", "HTML5"]
    },
    {
        "UserID": 3, "FirstName": "Charlie", "LastName": "Brown", "ProfessionalTitle": "Backend Engineer",
        "skills": ["Python", "Flask", "Django", "PostgreSQL", "Docker", "AWS"]
    },
    # Note: Recruiter accounts do not have a corresponding 'user' profile in this model
]

JOBS_DATA = [
    {
        "jobId": 1, "title": "Senior Data Scientist", "company": "Innovate Inc.", "location": "San Francisco, CA",
        "skillsRequired": ["Python", "Machine Learning", "PyTorch", "Big Data"], "recruiterId": 101
    },
    {
        "jobId": 2, "title": "React Frontend Developer", "company": "Creative Solutions", "location": "New York, NY",
        "skillsRequired": ["React", "TypeScript", "Redux", "CSS"], "recruiterId": 101
    },
    {
        "jobId": 3, "title": "Python Backend Developer", "company": "DataCorp", "location": "Austin, TX",
        "skillsRequired": ["Python", "Django", "REST APIs", "PostgreSQL"], "recruiterId": 101
    },
    # ... more jobs if you like
]

def seed_database():
    """Wipes and reseeds the database with sample accounts, users, and jobs."""
    print("Connecting to the database...")
    
    # Get collection objects
    accounts_col = db.accounts_collection()
    users_col = db.users_collection()
    jobs_col = db.jobs_collection()
    applications_col = db.applications_collection()
    counters_col = db.counters_collection()

    print("Wiping existing data...")
    accounts_col.delete_many({})
    users_col.delete_many({})
    jobs_col.delete_many({})
    applications_col.delete_many({})

    print("Seeding accounts...")
    accounts_to_insert = []
    for account in ACCOUNTS_DATA:
        hashed_password = auth_service.hash_password("password123")
        accounts_to_insert.append({
            "_id": account["_id"],
            "email": account["email"],
            "password": hashed_password,
            "role": account["role"],
            "createdAt": datetime.utcnow()
        })
    if accounts_to_insert:
        accounts_col.insert_many(accounts_to_insert)

    print(f"Seeding {len(USERS_DATA)} user profiles...")
    if USERS_DATA:
        users_col.insert_many(USERS_DATA)

    print(f"Seeding {len(JOBS_DATA)} jobs...")
    if JOBS_DATA:
        jobs_col.insert_many(JOBS_DATA)

    # Set counters to a value higher than our highest hardcoded ID
    print("Resetting counters...")
    counters_col.update_one({"_id": "UserID"}, {"$set": {"sequence_value": 200}}, upsert=True)
    counters_col.update_one({"_id": "jobId"}, {"$set": {"sequence_value": 200}}, upsert=True)
    counters_col.update_one({"_id": "appId"}, {"$set": {"sequence_value": 0}}, upsert=True)

    print("\n--- Database Seeding Complete! ---")
    print(f"-> {accounts_col.count_documents({})} accounts created.")
    print(f"-> {users_col.count_documents({})} user profiles created.")
    print(f"-> {jobs_col.count_documents({})} jobs created.")
    print("\nSample Users:")
    print("  - alice@example.com (user)")
    print("  - bob@example.com (user)")
    print("  - recruiter@corp.com (recruiter)")
    print("\nAll accounts have the password: 'password123'")

if __name__ == "__main__":
    seed_database()