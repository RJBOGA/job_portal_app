import json
import os
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

# If this file is executed directly with `python`, Streamlit will emit many
# warnings and session state won't work. Detect that case early and print a
# short user-friendly message instead of spamming the console.
try:
    # Available in recent Streamlit releases
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    if get_script_run_ctx() is None:
        # Not running under `streamlit run`.
        print("This app should be launched with `streamlit run src/frontend/app_streamlit.py` to use the interactive UI and session state.")
        raise SystemExit(0)
except Exception:
    # If the import fails or something unexpected happens, fall back to
    # continuing — we already handle missing secrets gracefully.
    pass

st.set_page_config(page_title="Job Seeker Chat", layout="wide")

# --- API Endpoints ---
def _get_secret_with_fallback(key: str, default: str) -> str:
    """Try to read a secret from Streamlit's secrets; if none exist, fall back to an
    environment variable and then to the provided default.

    This avoids Streamlit raising StreamlitSecretNotFoundError when running the
    script directly (outside of `streamlit run`).
    """
    try:
        # st.secrets may raise StreamlitSecretNotFoundError if no secrets.toml exists
        return st.secrets.get(key, os.getenv(key, default))
    except StreamlitSecretNotFoundError:
        return os.getenv(key, default)


NL2GQL_ENDPOINT = _get_secret_with_fallback("NL2GQL_ENDPOINT", "http://localhost:8000/nl2gql")
GRAPHQL_ENDPOINT = _get_secret_with_fallback("GRAPHQL_ENDPOINT", "http://localhost:8000/graphql")

# --- Helper Functions for Auth ---
def handle_login(email, password):
    query = f"""
    mutation {{
        login(email: \"{email}\", password: \"{password}\") {{
            token
        }}
    }}
    """
    try:
        r = requests.post(GRAPHQL_ENDPOINT, json={'query': query})
        if r.status_code == 200 and "errors" not in r.json().get('data', {}):
            data = r.json().get('data', {})
            if data and data.get('login'):
                st.session_state.token = data["login"]["token"]
                # Fetch user info and store in session state
                fetch_and_store_user_info()
                st.rerun()
            else:
                st.error(r.json().get("errors", [{}])[0].get("message", "Login failed."))
    except Exception as e:
        st.error(f"Connection error: {e}")

def handle_register(email, password, role):
    query = f"""
    mutation {{
        register(email: \"{email}\", password: \"{password}\", role: \"{role}\") {{
            token
        }}
    }}
    """
    try:
        r = requests.post(GRAPHQL_ENDPOINT, json={'query': query})
        response_json = r.json()
        
        # Check for GraphQL errors
        if "errors" in response_json:
            error_message = response_json["errors"][0]["message"]
            st.error(error_message)
            return

        # If no errors and we have data
        data = response_json.get('data', {})
        if data and data.get('register'):
            st.session_state.token = data["register"]["token"]
            # Fetch user info and store in session state
            fetch_and_store_user_info()
            st.rerun()
        else:
            st.error("Registration failed.")
    except Exception as e:
        st.error(f"Connection error: {e}")
# --- JWT decode helper ---
import base64
def decode_jwt_payload(token):
    try:
        payload_part = token.split(".")[1]
        # Pad base64 if needed
        rem = len(payload_part) % 4
        if rem:
            payload_part += '=' * (4 - rem)
        decoded = base64.urlsafe_b64decode(payload_part)
        return json.loads(decoded)
    except Exception:
        return {}

# --- Fetch user info after login/register ---
def fetch_and_store_user_info():
    token = st.session_state.get("token")
    if not token:
        return
    
    # First get basic info from token
    payload = decode_jwt_payload(token)
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")
    
    if not user_id:
        return
        
    # Store basic info from token
    st.session_state.user_email = email
    st.session_state.user_role = role
    
    # Fetch detailed user info if it's a job seeker
    if role == "user":
        query = f"""
        query {{
            userById(UserID: {user_id}) {{
                FirstName
                LastName
                ProfessionalTitle
                Summary
            }}
        }}
        """
        headers = {"Authorization": f"Bearer {token}"}
        try:
            r = requests.post(GRAPHQL_ENDPOINT, json={'query': query}, headers=headers)
            if r.status_code == 200:
                data = r.json().get('data', {})
                user = data.get('userById')
                if user:
                    full_name = f"{user.get('FirstName', '')} {user.get('LastName', '')}".strip()
                    st.session_state.user_name = full_name or email  # fallback to email if name not set
                    st.session_state.user_initials = (
                        (user.get('FirstName', '')[:1] + user.get('LastName', '')[:1]).upper()
                        if user.get('FirstName') and user.get('LastName')
                        else email[:2].upper()
                    )
                    # Store additional user details
                    st.session_state.user_title = user.get('ProfessionalTitle', '')
                    st.session_state.user_summary = user.get('Summary', '')
        except Exception as e:
            st.error(f"Connection error: {e}")
    else:  # For recruiters, use email as display name
        st.session_state.user_name = f"Recruiter: {email}"
        st.session_state.user_initials = "R"

def show_auth_page():
    st.title("Welcome to the AI Job Portal")
    
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                handle_login(email, password)
    
    with register_tab:
        with st.form("register_form"):
            email = st.text_input("Registration Email")
            password = st.text_input("Registration Password", type="password")
            role = st.selectbox("I am a...", ["user", "recruiter"], key="role_select")
            submitted = st.form_submit_button("Register")
            if submitted:
                handle_register(email, password, role)

def show_chat_page():

    st.title("AI Job Assistant")
    col1, col2 = st.columns([4, 1])
    with col2:
        # Show user info and logout
        user_name = st.session_state.get("user_name", "User")
        user_initials = st.session_state.get("user_initials", "U")
        user_role = st.session_state.get("user_role", "")
        user_title = st.session_state.get("user_title", "")
        
        # Create user info display with simpler layout
        st.markdown(
            f"""
            <div style='text-align:right;margin-bottom:1em;'>
                <div style='display:flex;align-items:center;justify-content:flex-end;gap:0.8em;'>
                    <span style='font-size:1.1em;color:#333;'>
                        {user_name}<br>
                        <span style='font-size:0.8em;color:#666;'>{user_role.capitalize()}</span>
                    </span>
                    <div style='background:#eee;border-radius:50%;width:2.2em;height:2.2em;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:1.2em;color:#333;'>
                        {user_initials}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("Logout", use_container_width=True):
            # Clear all user-related session state
            keys_to_clear = [
                "token", "user_name", "user_initials", "user_email",
                "user_role", "user_title", "user_summary", "messages"
            ]
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I help you today?"}]

    # Render chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Chat input
    user_prompt = st.chat_input("Ask me to find jobs, apply, or manage your profile.")
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            resp = requests.post(NL2GQL_ENDPOINT, json={"query": user_prompt}, headers=headers, timeout=90)
            
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
if "token" not in st.session_state:
    show_auth_page()
else:
    # If user info not loaded, fetch it
    if "user_name" not in st.session_state or "user_initials" not in st.session_state:
        fetch_and_store_user_info()
    show_chat_page()