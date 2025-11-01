import os
import requests
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '../../config/.env')
load_dotenv(dotenv_path=env_path)

from ..errors import json_error, unwrap_graphql_errors

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"

def build_nl2gql_prompt(user_text: str, schema_sdl: str) -> str:
    """Builds a non-restrictive prompt for the LLM with minimal authentication requirements."""
    return (
        "You are a GraphQL assistant for a job portal. Your job is to translate the user's request into a valid GraphQL operation based on the schema. "
        "Return ONLY the GraphQL operation code with no explanations.\n\n"
        "**KEY INSTRUCTIONS:**\n"
        "1. Most queries are public - freely use:\n"
        "   - `users` and `userById` for user searches\n"
        "   - `jobs` and `jobById` for job searches\n"
        "   - `matchingCandidates` for candidate matching\n"
        "   - `analyticsJobsCount` for job counts\n\n"
        "2. Auth-required operations - use these if the request implies it's the logged-in user acting:\n"
        "   - `updateMyProfile` for profile updates like 'update my skills'\n"
        "   - `apply` for job applications like 'apply to job X'\n"
        "   - `recommendedJobs` for personalized recommendations\n\n"
        "3. Admin operations (no role restrictions) - use if explicitly requested:\n"
        "   - `createJob` for creating jobs\n"
        "   - `updateJob`/`deleteJob` for managing jobs\n"
        "   - `updateUser`/`deleteUser` for managing other users\n\n"
        "4. If the request cannot be mapped to the schema, return the word: INVALID\n\n"
        "Schema:\n"
        f"{schema_sdl}\n\n"
        "User request:\n"
        f"{user_text}"
    )

# ... (The rest of the file - extract_graphql and process_nl2gql_request - has NO CHANGES)
def extract_graphql(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            block = parts[i]
            if block.strip().startswith("graphql"):
                lines = block.splitlines()
                return "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        for i in range(1, len(parts), 2):
            if parts[i].strip():
                return parts[i].strip()
    return text.strip()

def process_nl2gql_request(user_text: str, schema_sdl: str, run_graphql: bool, graphql_executor_fn, user_context: dict | None = None):
    # Role parameter removed - not needed in non-RBAC MVP
    prompt = build_nl2gql_prompt(user_text, schema_sdl)
    headers = {}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    try:
        resp = requests.post(
            OLLAMA_GENERATE_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            headers=headers,
            timeout=90,
        )
    except requests.exceptions.Timeout:
        return json_error("Upstream NL generation timed out", 504)
    except requests.exceptions.RequestException as e:
        return json_error(f"Ollama network error: {e}", 502)
    if not resp.ok:
        return json_error(f"Ollama error {resp.status_code}", 502)
    try:
        gen_body = resp.json()
    except ValueError:
        return json_error("Ollama returned non-JSON response", 502)
    gen = gen_body.get("response", "")
    gql = extract_graphql(gen)
    if not gql or gql.strip().upper() == "INVALID":
        return json_error(
            "Out of scope. Your request could not be mapped to a valid operation. Try asking about users or jobs.",
            400
        )
    if not run_graphql:
        return {"graphql": gql}, 200
    success, result = graphql_executor_fn({"query": gql})
    wrapped_error = unwrap_graphql_errors(result)
    if wrapped_error:
        return wrapped_error
    return {"graphql": gql, "result": result}, (200 if success else 400)
