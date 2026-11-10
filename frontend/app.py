"""Streamlit frontend for the Cloud-Based API Key Access Management API.

Run:   streamlit run frontend/app.py
Env:   API_URL  (default http://localhost:8000)
"""
import os

import requests
import streamlit as st
from jose import jwt

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="API Key Manager", page_icon="🔑", layout="wide")

# Streamlit reruns this script on every click; session_state survives reruns.
for _key, _default in {
    "token": None,        # JWT from /user/login
    "claims": None,       # decoded JWT payload: id, username, role
    "is_admin": False,
    "reset_token": None,  # JWT from /forgot/password, used by /reset/password
    "reset_user": "",
}.items():
    st.session_state.setdefault(_key, _default)


# ======================================================================
# Helpers
# ======================================================================
def api(method, path, body=None, token=None, quiet=False):
    """Send one HTTP request to the FastAPI backend.

    Attaches the Bearer token (explicit `token` or the logged-in one).
    Returns the parsed JSON on success, or None on error (shown in the UI
    unless quiet=True).
    """
    token = token or st.session_state.token
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.request(method, API_URL + path, json=body, headers=headers, timeout=15)
    except requests.RequestException as exc:
        if not quiet:
            st.error(f"Cannot reach backend at {API_URL}: {exc}")
        return None

    try:
        data = r.json()
    except ValueError:
        data = r.text

    if r.ok:
        return data
    if quiet:
        return None

    detail = data.get("detail", data) if isinstance(data, dict) else data
    if r.status_code == 401 and st.session_state.token and token == st.session_state.token:
        logout()
        st.warning("Your session has expired. Please log in again.")
    st.error(f"Error {r.status_code}: {detail}")
    return None


def show_result(res):
    """Render a backend response as a success / error / warning message."""
    if res is None:
        return False
    if isinstance(res, dict):
        if res.get("status") == "fail":
            st.error(res.get("message", "Request failed"))
            return False
        st.success(res.get("message", "Done"))
        return True
    # Some endpoints return a bare string, e.g. "User already exists".
    st.warning(str(res))
    return False


def without_password(user):
    """Never display password hashes returned by the backend."""
    return {k: v for k, v in user.items() if k != "password"}


def parse_ids(text):
    """Turn '1, 2,3' into [1, 2, 3]; returns None and shows an error if invalid."""
    try:
        return [int(x) for x in text.split(",") if x.strip()]
    except ValueError:
        st.error("User IDs must be whole numbers separated by commas, e.g. 1, 2, 3")
        return None


def mask(key):
    return key[:6] + "•" * 20 + key[-4:] if isinstance(key, str) and len(key) > 10 else key


def my_id():
    return st.session_state.claims["id"]


def logout():
    st.session_state.token = None
    st.session_state.claims = None
    st.session_state.is_admin = False
    st.session_state.pop("all_keys", None)


# ======================================================================
# 1. Sign up
# ======================================================================
def signup_page():
    st.title("📝 Sign up")
    with st.form("signup", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create account", type="primary")

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            # POST /create/user  ->  createUser()
            if show_result(api("POST", "/create/user", {"username": username, "password": password})):
                st.info("Account created. Go to **Login** to sign in.")


# ======================================================================
# 2. Login
# ======================================================================
def login_page():
    st.title("🔐 Login")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")

    if not submitted:
        return

    # POST /user/login  ->  login()
    res = api("POST", "/user/login", {"form_username": username, "form_password": password})
    if not res:
        return
    if not res.get("access_token"):
        st.error(res.get("message", "Login failed"))
        return

    st.session_state.token = res["access_token"]
    # Decoded only to read id/username for the UI; the backend still verifies it.
    st.session_state.claims = jwt.get_unverified_claims(res["access_token"])
    # The JWT holds a role *id*, not a name, so probe an admin-only endpoint
    # once to learn whether this user is an admin (controls which pages show).
    st.session_state.is_admin = api("GET", "/get/all/users", quiet=True) is not None
    st.rerun()


# ======================================================================
# 4. Forgot password / reset password
# ======================================================================
def forgot_password_page():
    st.title("🔁 Forgot password")

    st.subheader("Step 1 — Request a reset")
    with st.form("forgot"):
        username = st.text_input("Username", value=st.session_state.reset_user)
        submitted = st.form_submit_button("Request reset")
    if submitted:
        # POST /forgot/password  ->  forgotPassword(); returns a short-lived token
        res = api("POST", "/forgot/password", {"username": username})
        if res and res.get("access_token"):
            st.session_state.reset_token = res["access_token"]
            st.session_state.reset_user = username
            st.success(res.get("message", "Reset requested."))

    if not st.session_state.reset_token:
        st.caption("Complete step 1 to unlock step 2.")
        return

    st.subheader("Step 2 — Set a new password")
    with st.form("reset"):
        username = st.text_input("Re-enter your username", value=st.session_state.reset_user)
        new_pw = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Reset password", type="primary")
    if submitted:
        if not new_pw or new_pw != confirm:
            st.error("Passwords are empty or do not match.")
            return
        # POST /reset/password  ->  resetPassword(); authorised by the reset token
        res = api("POST", "/reset/password", {"username": username, "password": new_pw},
                  token=st.session_state.reset_token)
        if show_result(res):
            st.session_state.reset_token = None
            st.session_state.reset_user = ""
            st.info("Password changed. Go to **Login** to sign in.")


# ======================================================================
# 3. Users
# ======================================================================
def all_users_page():
    st.title("👥 All users")
    if st.button("Get all users", type="primary"):
        # GET /get/all/users  ->  getAllUsers()  (admin only)
        users = api("GET", "/get/all/users")
        if users is not None:
            st.dataframe([without_password(u) for u in users], hide_index=True)


def get_user_page():
    st.title("🔎 Get user")
    if st.session_state.is_admin:
        user_id = st.number_input("User ID", min_value=1, step=1, value=my_id())
    else:
        st.caption("You can view your own profile.")
        user_id = my_id()

    if st.button("Get user", type="primary"):
        # GET /get/user/{id}  ->  getUser()  (admin, or the user themselves)
        user = api("GET", f"/get/user/{int(user_id)}")
        if user:
            st.json(without_password(user))


def update_user_page():
    st.title("✏️ Update my account")
    st.caption(f"Updating user ID {my_id()}. Both fields are required by the API.")
    with st.form("update_user"):
        username = st.text_input("New username", value=st.session_state.claims["username"])
        password = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Update", type="primary")

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            # Admins and users have separate update endpoints in the backend.
            path = f"/update/admin/{my_id()}" if st.session_state.is_admin else f"/update/user/{my_id()}"
            if show_result(api("PUT", path, {"username": username, "password": password})):
                st.info("Log out and back in to refresh your session details.")


def delete_user_page():
    st.title("🗑️ Delete user")
    if st.session_state.is_admin:
        user_id = int(st.number_input("User ID to delete", min_value=1, step=1))
    else:
        st.caption("You can delete your own account.")
        user_id = my_id()

    confirm = st.checkbox(f"Yes, permanently delete user {user_id}")
    if st.button("Delete user", type="primary", disabled=not confirm):
        # DELETE /delete/user/{id}  ->  deleteUser()  (admin, or the user themselves)
        if show_result(api("DELETE", f"/delete/user/{user_id}")) and user_id == my_id():
            logout()
            st.rerun()


# ======================================================================
# 5. API keys
# ======================================================================
def view_keys_page():
    st.title("🔑 My API keys")
    reveal = st.toggle("Reveal keys")
    if st.session_state.is_admin:
        # The backend's admin branch of /get/user/keys/{id} calls getAllKeys()
        # without arguments and fails, so admins use /get/all/keys directly.
        keys = api("GET", "/get/all/keys")
        keys = [k["key"] for k in keys] if keys is not None else None
    else:
        # GET /get/user/keys/{id}  ->  getUserPermittedKeys()
        keys = api("GET", f"/get/user/keys/{my_id()}")

    if keys is None:
        return
    if not keys:
        st.info("No API keys have been shared with you yet.")
    for key in keys:
        st.code(key if reveal else mask(key), language=None)


def generate_key_page():
    st.title("➕ Generate API key")
    with st.form("new_key"):
        ids_text = st.text_input("Permitted user IDs (comma-separated)", placeholder="e.g. 2, 3, 5")
        submitted = st.form_submit_button("Generate", type="primary")
    if submitted:
        ids = parse_ids(ids_text)
        if ids is not None:
            # POST /create/key  ->  createApiKey()  (admin only)
            show_result(api("POST", "/create/key", {"permitted_users": ids}))


def all_keys_page():
    st.title("📋 All API keys")
    reveal = st.toggle("Reveal keys")
    if st.button("Get all API keys", type="primary"):
        # GET /get/all/keys  ->  getAllKeys()  (admin only)
        st.session_state.all_keys = api("GET", "/get/all/keys")
    keys = st.session_state.get("all_keys")
    if keys is not None:
        rows = [{**k, "key": k["key"] if reveal else mask(k["key"])} for k in keys]
        st.dataframe(rows, hide_index=True)


def get_key_page():
    st.title("🔎 Get API key")
    key_id = int(st.number_input("Key ID", min_value=1, step=1))
    if st.button("Get key", type="primary"):
        # GET /get/key/{id}  ->  getKey()  (admin only)
        key = api("GET", f"/get/key/{key_id}")
        if key:
            st.json(key)


def _pick_key(label):
    """Selectbox of existing key IDs, loaded from /get/all/keys."""
    keys = api("GET", "/get/all/keys")
    if not keys:
        st.info("No API keys exist yet.")
        return None
    by_id = {k["id"]: k for k in keys}
    key_id = st.selectbox(label, list(by_id),
                          format_func=lambda i: f"#{i} — users {by_id[i]['permitted_users']}")
    return by_id[key_id]


def update_key_page():
    st.title("✏️ Update API key")
    key = _pick_key("Key to update")
    if not key:
        return
    with st.form("update_key"):
        current = ", ".join(str(u) for u in key["permitted_users"] or [])
        ids_text = st.text_input("Permitted user IDs (comma-separated)", value=current)
        submitted = st.form_submit_button("Update", type="primary")
    if submitted:
        ids = parse_ids(ids_text)
        if ids is not None:
            # PUT /update/key/{id}  ->  updateKey()  (admin only)
            show_result(api("PUT", f"/update/key/{key['id']}", {"permitted_users": ids}))


def delete_key_page():
    st.title("🗑️ Delete API key")
    key = _pick_key("Key to delete")
    if not key:
        return
    confirm = st.checkbox(f"Yes, permanently delete key #{key['id']}")
    if st.button("Delete key", type="primary", disabled=not confirm):
        # DELETE /delete/key/{id}  ->  deleteKey()  (admin only)
        if show_result(api("DELETE", f"/delete/key/{key['id']}")):
            st.rerun()


# ======================================================================
# Navigation — pages shown depend on login state and role
# ======================================================================
if not st.session_state.token:
    pages = {
        "Welcome": [
            st.Page(login_page, title="Login", icon="🔐", default=True),
            st.Page(signup_page, title="Sign up", icon="📝"),
            st.Page(forgot_password_page, title="Forgot password", icon="🔁"),
        ]
    }
else:
    admin = st.session_state.is_admin
    user_pages = [
        st.Page(get_user_page, title="Get user" if admin else "My profile", icon="🔎", default=True),
        st.Page(update_user_page, title="Update my account", icon="✏️"),
        st.Page(delete_user_page, title="Delete user" if admin else "Delete my account", icon="🗑️"),
    ]
    key_pages = [st.Page(view_keys_page, title="View API keys", icon="🔑")]
    if admin:
        user_pages.insert(0, st.Page(all_users_page, title="All users", icon="👥"))
        key_pages += [
            st.Page(generate_key_page, title="Generate key", icon="➕"),
            st.Page(all_keys_page, title="All keys", icon="📋"),
            st.Page(get_key_page, title="Get key", icon="🔎"),
            st.Page(update_key_page, title="Update key", icon="✏️"),
            st.Page(delete_key_page, title="Delete key", icon="🗑️"),
        ]
    pages = {"Users": user_pages, "API keys": key_pages}

    c = st.session_state.claims
    st.sidebar.markdown(f"Signed in as **{c['username']}**  \nID {c['id']} · {'Admin' if admin else 'User'}")
    st.sidebar.button("Logout", on_click=logout)

st.navigation(pages).run()
