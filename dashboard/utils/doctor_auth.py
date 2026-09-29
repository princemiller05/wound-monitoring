"""
doctor_auth.py
--------------
Email/password login for doctors using the SAME Firebase Auth the patient app
uses, via Firebase's Identity Toolkit REST API (Streamlit can't use the Firebase
client SDK directly).

The Web API key is a public client key (safe to ship, like in a mobile app) —
the password itself is only ever sent to Google over HTTPS, never stored by us.

Config: FIREBASE_WEB_API_KEY in .streamlit/secrets.toml (or env).
"""

import os

import requests
import streamlit as st

_BASE = "https://identitytoolkit.googleapis.com/v1/accounts"


def _api_key() -> str:
    try:
        if "FIREBASE_WEB_API_KEY" in st.secrets:
            return str(st.secrets["FIREBASE_WEB_API_KEY"])
    except Exception:
        pass
    return os.getenv("FIREBASE_WEB_API_KEY", "")


def auth_configured() -> bool:
    return bool(_api_key())


_FRIENDLY = {
    "EMAIL_NOT_FOUND": "No account with that email.",
    "INVALID_PASSWORD": "Incorrect password.",
    "INVALID_LOGIN_CREDENTIALS": "Incorrect email or password.",
    "USER_DISABLED": "This account has been disabled.",
    "EMAIL_EXISTS": "An account with that email already exists.",
    "WEAK_PASSWORD : Password should be at least 6 characters":
        "Password must be at least 6 characters.",
    "INVALID_EMAIL": "That email address isn't valid.",
}


def _friendly(err: str) -> str:
    return _FRIENDLY.get(err, err or "Authentication failed.")


def _post(action: str, email: str, password: str):
    key = _api_key()
    if not key:
        return None, "Login isn't configured (missing FIREBASE_WEB_API_KEY)."
    try:
        r = requests.post(
            f"{_BASE}:{action}?key={key}",
            json={"email": email.strip(), "password": password,
                  "returnSecureToken": True},
            timeout=20,
        )
        data = r.json()
        if r.status_code == 200:
            return data, None
        msg = (data.get("error", {}) or {}).get("message", "")
        return None, _friendly(msg)
    except Exception as exc:
        return None, f"Network error: {exc}"


def sign_in(email: str, password: str):
    """Returns (email, None) on success or (None, error_message)."""
    data, err = _post("signInWithPassword", email, password)
    if err:
        return None, err
    return (data.get("email") or email).strip().lower(), None


def sign_up(email: str, password: str):
    """Create a new doctor account. Returns (email, None) or (None, error)."""
    data, err = _post("signUp", email, password)
    if err:
        return None, err
    return (data.get("email") or email).strip().lower(), None
