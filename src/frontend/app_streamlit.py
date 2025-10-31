import json
import os
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

# --- Startup Check ---
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if get_script_run_ctx() is None:
        print("This app should be launched with `streamlit run src/frontend/app_streamlit.py`")
        raise SystemExit(0)
except Exception:
    pass

st.set_page_config(page_title="Job Seeker Chat", layout="wide")

# --- API Endpoints ---
def _get_secret_with_fallback(key: str, default: str) -> str:
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except StreamlitSecretNotFoundError:
        return os.getenv(key, default)

NL2GQL_ENDPOINT = _get_secret_with_fallback("NL2GQL_ENDPOINT", "http://localhost:8000/nl2gql")
GRAPHQL_ENDPOINT = _get_secret_with_fallback("GRAPHQL_ENDPOINT", "http://localhost:8000/graphql")

# --- Helper functions are no longer needed for auth flow but kept for later ---
def handle_login(email, password): pass
def handle_register(email, password, role): pass
def show_auth_page(): pass
import base64
def decode_jwt_payload(token): pass
def fetch_and_store_user_info(): pass

# --- Main Chat Page ---
def show_chat_page():
    st.title("AI Job Assistant (Auth Disabled)")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! Authentication is disabled. How can I help you today?"}]

    # Render chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Chat input
    user_prompt = st.chat_input("Ask me anything about users, jobs, or applications.")
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        try:
            # --- AUTH DISABLED: No headers are sent ---
            resp = requests.post(NL2GQL_ENDPOINT, json={"query": user_prompt}, timeout=90)
            
            data = resp.json()
            if resp.status_code != 200:
                err_msg = data.get("error", {}).get("message", "An unknown error occurred.")
                assistant_text = f"**Error:** {err_msg}"
            else:
                gql = data.get("graphql", "")
                result = data.get("result", {})
                assistant_text = (
                    f"**Generated GraphQL:**\n\n```graphql\n{gql}\n```\n\n"
                    f"**Result:**\n\n```json\n{json.dumps(result, indent=2)}\n```"
                )
        except requests.exceptions.ConnectionError:
            assistant_text = "Error: Could not connect to the backend service. Is it running?"
        except Exception as e:
            assistant_text = f"An unexpected error occurred: {e}"

        with st.chat_message("assistant"):
            st.markdown(assistant_text)
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

# --- Main App Logic ---
# Bypassing auth and showing the chat page directly
show_chat_page()