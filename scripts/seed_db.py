import sys
import os
from datetime import datetime

# --- This is a crucial step to make sure we can import from the `src` directory ---
# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# ---------------------------------------------------------------------------------

# Now we can import our database module
from src.backend import db

# --- Sample Data ---

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
    {
        "UserID": 4, "FirstName": "Diana", "LastName": "Miller", "ProfessionalTitle": "Full Stack Developer",
        "skills": ["Python", "JavaScript", "React", "Flask", "Docker", "SQL"]
    },
    {
        "UserID": 5, "FirstName": "Ethan", "LastName": "Davis", "ProfessionalTitle": "DevOps Engineer",
        "skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD"]
    },
    {
        "UserID": 6, "FirstName": "Fiona", "LastName": "Garcia", "ProfessionalTitle": "UX Designer",
        "skills": ["Figma", "Sketch", "User Research", "Prototyping"]
    },
    {
        "UserID": 7, "FirstName": "George", "LastName": "Rodriguez", "ProfessionalTitle": "Data Analyst",
        "skills": ["SQL", "Tableau", "Excel", "Python", "Pandas"]
    },
    {
        "UserID": 8, "FirstName": "Hannah", "LastName": "Wilson", "ProfessionalTitle": "Mobile Developer",
        "skills": ["Swift", "Kotlin", "iOS", "Android", "React Native"]
    },
    {
        "UserID": 9, "FirstName": "Ian", "LastName": "Martinez", "ProfessionalTitle": "Machine Learning Engineer",
        "skills": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "MLOps"]
    },
    {
        "UserID": 10, "FirstName": "Jane", "LastName": "Anderson", "ProfessionalTitle": "Product Manager",
        "skills": ["Agile", "Scrum", "Roadmapping", "JIRA"]
    }
]

JOBS_DATA = [
    {
        "jobId": 1, "title": "Senior Data Scientist", "company": "Innovate Inc.", "location": "San Francisco, CA",
        "skillsRequired": ["Python", "Machine Learning", "PyTorch", "Big Data"]
    },
    {
        "jobId": 2, "title": "React Frontend Developer", "company": "Creative Solutions", "location": "New York, NY",
        "skillsRequired": ["React", "TypeScript", "Redux", "CSS"]
    },
    {
        "jobId": 3, "title": "Python Backend Developer", "company": "DataCorp", "location": "Austin, TX",
        "skillsRequired": ["Python", "Django", "REST APIs", "PostgreSQL"]
    },
    {
        "jobId": 4, "title": "Cloud DevOps Engineer", "company": "SkyHigh Cloud", "location": "Seattle, WA",
        "skillsRequired": ["AWS", "Kubernetes", "Docker", "Terraform"]
    },
    {
        "jobId": 5, "title": "Full Stack Engineer (Python/React)", "company": "Innovate Inc.", "location": "Remote",
        "skillsRequired": ["Python", "React", "Flask", "SQL", "Docker"]
    },
    {
        "jobId": 6, "title": "Lead Mobile Engineer (iOS)", "company": "Appify", "location": "Cupertino, CA",
        "skillsRequired": ["Swift", "iOS", "Xcode", "UIKit"]
    },
    {
        "jobId": 7, "title": "Junior Data Analyst", "company": "DataCorp", "location": "Austin, TX",
        "skillsRequired": ["SQL", "Excel", "Tableau"]
    },
    {
        "jobId": 8, "title": "Machine Learning Research Scientist", "company": "AI Future", "location": "Boston, MA",
        "skillsRequired": ["Python", "TensorFlow", "Research", "PhD"]
    },
    {
        "jobId": 9, "title": "Web Developer", "company": "Creative Solutions", "location": "New York, NY",
        "skillsRequired": ["HTML5", "CSS", "JavaScript"]
    },
    {
        "jobId": 10, "title": "Senior Backend Engineer (Go)", "company": "ScaleFast", "location": "Remote",
        "skillsRequired": ["Go", "Microservices", "gRPC", "Kubernetes"]
    }
]

def seed_data():
    """Wipes and reseeds the database with sample data."""
    print("Connecting to the database...")
    
    # Get collection objects
    users_col = db.users_collection()
    jobs_col = db.jobs_collection()
    applications_col = db.applications_collection()
    counters_col = db.counters_collection()
    accounts_col = db.accounts_collection()

    print("Wiping existing collections...")
    users_col.delete_many({})
    jobs_col.delete_many({})
    applications_col.delete_many({})
    accounts_col.delete_many({})

    print("Resetting counters...")
    counters_col.update_one({"_id": "UserID"}, {"$set": {"sequence_value": 10}}, upsert=True)
    counters_col.update_one({"_id": "jobId"}, {"$set": {"sequence_value": 10}}, upsert=True)
    counters_col.update_one({"_id": "appId"}, {"$set": {"sequence_value": 0}}, upsert=True)

    print(f"Inserting {len(USERS_DATA)} users...")
    if USERS_DATA:
        users_col.insert_many(USERS_DATA)

    print(f"Inserting {len(JOBS_DATA)} jobs...")
    if JOBS_DATA:
        jobs_col.insert_many(JOBS_DATA)

    print("\nDatabase seeded successfully!")
    print(f"-> {users_col.count_documents({})} users")
    print(f"-> {jobs_col.count_documents({})} jobs")
    print(f"-> {applications_col.count_documents({})} applications")

if __name__ == "__main__":
    seed_data()