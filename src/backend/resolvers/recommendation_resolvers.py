# src/backend/resolvers/recommendation_resolvers.py

from ariadne import QueryType
from ..repository import user_repo, job_repo
from ..db import jobs_collection

query = QueryType()

# --- Skill Matching Algorithm ---
def calculate_match_score(candidate_skills, required_skills):
    """
    Calculates a simple match score based on the percentage of required skills
    that the candidate possesses.
    """
    if not required_skills:
        return 0 # Cannot match if a job has no required skills
        
    # Find the intersection of the two sets of skills
    matching_skills = set(candidate_skills or []).intersection(set(required_skills or []))
    
    score = (len(matching_skills) / len(required_skills)) * 100
    return int(score)

# --- Smart Query Resolvers ---

@query.field("recommendedJobs")
def resolve_recommended_jobs(_, info, skillMatchThreshold=50):
    user = info.context.get("user")
    if not user or user.get("role") != "user":
        raise PermissionError("Access denied: You must be logged in as a 'user' to get job recommendations.")
    
    user_id = user.get("sub")
    candidate = user_repo.find_one_by_id(user_id)
    if not candidate or not candidate.get("skills"):
        # Return empty list if user has no profile or no skills listed
        return []
        
    candidate_skills = candidate.get("skills")
    
    # Fetch all jobs to compare against.
    # In a production app with millions of jobs, you'd use a more advanced search index (like Elasticsearch).
    # For our scale, this is perfectly fine.
    all_jobs = job_repo.find_jobs({}, None, None)
    
    matched_jobs = []
    for job in all_jobs:
        required_skills = job.get("skillsRequired")
        score = calculate_match_score(candidate_skills, required_skills)
        
        if score >= skillMatchThreshold:
            # Add the score to the job object so we can sort by it (optional but useful)
            job_with_score = {**job, "matchScore": score}
            matched_jobs.append(job_with_score)
            
    # Sort the jobs from the highest match score to the lowest
    matched_jobs.sort(key=lambda j: j["matchScore"], reverse=True)
    
    return [job_repo.to_job_output(j) for j in matched_jobs]


@query.field("matchingCandidates")
def resolve_matching_candidates(_, info, jobId, skillMatchThreshold=50):
    user = info.context.get("user")
    if not user or user.get("role") != "recruiter":
        raise PermissionError("Access denied: Only recruiters can find matching candidates.")
        
    job = job_repo.find_job_by_id(jobId)
    if not job or not job.get("skillsRequired"):
        return [] # Return empty if job not found or has no skills
        
    required_skills = job.get("skillsRequired")
    
    # Fetch all users to compare against
    all_users = user_repo.find_users({}, None, None)
    
    matched_users = []
    for candidate in all_users:
        candidate_skills = candidate.get("skills")
        score = calculate_match_score(candidate_skills, required_skills)
        
        if score >= skillMatchThreshold:
            user_with_score = {**candidate, "matchScore": score}
            matched_users.append(user_with_score)
            
    # Sort by best match
    matched_users.sort(key=lambda u: u["matchScore"], reverse=True)
    
    return [user_repo.to_user_output(u) for u in matched_users]


@query.field("analyticsJobsCount")
def resolve_analytics_jobs_count(_, info, location=None, company=None):
    # This query can be public or restricted
    
    # Build a filter using the same logic as our regular job search
    job_filter = job_repo.build_job_filter(company, location, None)
    
    # Use MongoDB's efficient count_documents method
    count = jobs_collection().count_documents(job_filter)
    
    return count