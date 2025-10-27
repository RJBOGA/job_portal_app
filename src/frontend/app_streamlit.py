import json
import os
import requests
import streamlit as st

st.set_page_config(page_title="Job Seeker Chat", layout="wide")

# --- API Endpoints ---
NL2GQL_ENDPOINT = st.secrets.get("NL2GQL_ENDPOINT", "http://localhost:8000/nl2gql")
GRAPHQL_ENDPOINT = st.secrets.get("GRAPHQL_ENDPOINT", "http://localhost:8000/graphql")

# --- Helper Functions for Auth ---
def handle_login(email, password):
    query = f"""
    mutation {{
        login(email: "{email}", password: "{password}") {{
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
                st.rerun()
            else:
                # Handle GraphQL errors that come in a 200 response
                st.error(r.json().get("errors", [{}])[0].get("message", "Login failed."))
    except Exception as e:
        st.error(f"Connection error: {e}")

def handle_register(email, password, role):
    query = f"""
    mutation {{
        register(email: "{email}", password: "{password}", role: "{role}") {{
            token
        }}
    }}
    """
    try:
        r = requests.post(GRAPHQL_ENDPOINT, json={'query': query})
        if r.status_code == 200 and "errors" not in r.json().get('data', {}):
            data = r.json().get('data', {})
            if data and data.get('register'):
                st.session_state.token = data["register"]["token"]
                st.rerun()
            else:
                st.error(r.json().get("errors", [{}])[0].get("message", "Registration failed."))
    except Exception as e:
        st.error(f"Connection error: {e}")

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
        if st.button("Logout", use_container_width=True):
            if "token" in st.session_state:
                del st.session_state.token
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
    show_chat_page()