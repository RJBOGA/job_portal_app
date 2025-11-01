import os
import sys
# Add project root (src/) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from ariadne import load_schema_from_path, make_executable_schema, graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from src.backend.services import auth_service

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../config/.env'))

# Import modules from the project structure
from src.backend.errors import (
    handle_http_exception, handle_value_error, handle_generic_exception, json_error
)
from src.backend.services.nl2gql_service import process_nl2gql_request
from src.backend.resolvers.user_resolvers import query as user_query, mutation as user_mutation
from src.backend.resolvers.job_resolvers import query as job_query, mutation as job_mutation
from src.backend.resolvers.application_resolvers import query as app_query, mutation as app_mutation, application as application_object
from src.backend.resolvers.auth_resolvers import mutation as auth_mutation
from src.backend.resolvers.recommendation_resolvers import query as recommendation_query
from src.backend.db import ensure_user_counter, ensure_job_counter, ensure_application_counter

# --- Flask app setup ---
app = Flask(__name__)
CORS(app)
explorer_html = ExplorerGraphiQL().html(None)

# --- Authentication Middleware (RE-ENABLED) ---
@app.before_request
def authenticate_request():
    """Verify JWT from Authorization header and attach payload to Flask's global `g` object."""
    if not hasattr(g, 'user'):
        g.user = None
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        g.user = auth_service.verify_token(token)

# --- Load and build GraphQL schema ---
schema_path = os.path.join(os.path.dirname(__file__), "schema.graphql")
type_defs = load_schema_from_path(schema_path)

schema = make_executable_schema(
    type_defs,
    [user_query, job_query, app_query, recommendation_query],
    [user_mutation, job_mutation, app_mutation, auth_mutation],
    application_object
)

# Initialize database counters
ensure_user_counter()
ensure_job_counter()
ensure_application_counter()

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    payload, status = json_error("Not found", 404)
    return jsonify(payload), status
@app.errorhandler(405)
def method_not_allowed(e):
    payload, status = json_error("Method not allowed", 405)
    return jsonify(payload), status
@app.errorhandler(ValueError)
def value_error(e):
    return handle_value_error(e)
@app.errorhandler(Exception)
def unhandled_exception(e):
    if isinstance(e, HTTPException): return handle_http_exception(e)
    return handle_generic_exception(e)

# --- API Endpoints ---
@app.route("/graphql", methods=["GET"])
def graphql_explorer():
    return explorer_html, 200

@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        payload, status = json_error("Body must be JSON with 'query' and optional 'variables'", 400)
        return jsonify(payload), status
    
    success, result = graphql_sync(schema, data, context_value={"request": request, "user": g.user}, debug=app.debug)
    return jsonify(result), (200 if success else 400)

@app.route("/")
def health():
    return jsonify({"status": "Backend is running!"}), 200

@app.route("/nl2gql", methods=["POST"])
def nl2gql():
    data = request.get_json(silent=True) or {}
    user_text = data.get("query", "")
    run_graphql = request.args.get("run", "true").lower() != "false"

    if not user_text.strip():
        payload, status = json_error("Missing 'query' in body", 400)
        return jsonify(payload), status

    schema_for_llm_path = os.path.join(os.path.dirname(__file__), "schema_for_llm.graphql")
    try:
        with open(schema_for_llm_path, "r", encoding="utf-8") as f:
            schema_sdl = f.read()
    except Exception as e:
        payload, status = json_error(f"Failed to read LLM schema file: {e}", 500)
        return jsonify(payload), status

    def execute_graphql_query(gql_data):
        return graphql_sync(schema, gql_data, context_value={"request": request, "user": g.user}, debug=app.debug)

    payload, status_code = process_nl2gql_request(
        user_text, schema_sdl, run_graphql, execute_graphql_query, g.user
    )
    return jsonify(payload), status_code

if __name__ == "__main__":
    print("🚀 Starting Flask server on http://localhost:8000 ...")
    app.run(host="0.0.0.0", port=8000, debug=True)