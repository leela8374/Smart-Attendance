"""
Authentication routes – login & logout for all roles.
"""

import hashlib
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template, flash,
)
from db import get_user_by_username

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─── Login ───────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_username(username)
        if user and user["password_hash"] == hash_password(password):
            if not user.get("is_active", True):
                flash("Your account is deactivated.", "error")
                return redirect(url_for("auth.login_page"))

            session["user_id"]   = user["user_id"]
            session["username"]  = user["username"]
            session["role"]      = user["role"]
            session["full_name"] = user["full_name"]

            role = user["role"]
            if role == "faculty":
                return redirect(url_for("faculty.dashboard"))
            elif role == "student":
                return redirect(url_for("student.dashboard"))
            else:
                return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


# ─── Logout ──────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login_page"))
