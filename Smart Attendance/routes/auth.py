"""
Authentication routes – login, register & logout for all roles.
"""

import hashlib
import logging
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template, flash,
)
from db import get_user_by_username, create_user, username_exists

auth_bp = Blueprint("auth", __name__)
logger  = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─── Login ────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if session.get("role"):                          # already logged in
        return _redirect_by_role(session["role"])

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            user = get_user_by_username(username)
        except Exception as e:
            logger.error("DynamoDB error on login: %s", e)
            flash("Service temporarily unavailable. Please try again.", "error")
            return render_template("login.html")

        if user and user["password_hash"] == hash_password(password):
            if not user.get("is_active", True):
                flash("Your account has been deactivated.", "error")
                return render_template("login.html")

            session["user_id"]   = user["user_id"]
            session["username"]  = user["username"]
            session["role"]      = user["role"]
            session["full_name"] = user["full_name"]
            flash(f"Welcome back, {user['full_name']}! 👋", "success")
            return _redirect_by_role(user["role"])
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


# ─── Register ─────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register_page():
    if session.get("role"):
        return _redirect_by_role(session["role"])

    if request.method == "POST":
        full_name  = request.form.get("full_name",  "").strip()
        username   = request.form.get("username",   "").strip()
        email      = request.form.get("email",      "").strip()
        password   = request.form.get("password",   "")
        confirm_pw = request.form.get("confirm_pw", "")
        role       = request.form.get("role",       "student")

        # ── Validation ──────────────────────────────────────────────────────
        errors = []
        if not all([full_name, username, email, password, confirm_pw]):
            errors.append("All fields are required.")
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_pw:
            errors.append("Passwords do not match.")
        if role not in ("student", "faculty"):
            errors.append("Invalid role selected.")

        if not errors:
            try:
                if username_exists(username):
                    errors.append("Username already taken. Please choose another.")
            except Exception as e:
                logger.error("DynamoDB error on register check: %s", e)
                flash("Service temporarily unavailable. Please try again.", "error")
                return render_template("register.html")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html",
                                   form=request.form)  # repopulate fields

        # ── Create account ───────────────────────────────────────────────────
        try:
            create_user(
                username      = username,
                password_hash = hash_password(password),
                role          = role,
                email         = email,
                full_name     = full_name,
            )
            flash(
                f"Account created successfully! Welcome, {full_name}. "
                f"Please login below.",
                "success",
            )
            return redirect(url_for("auth.login_page"))
        except Exception as e:
            logger.error("Failed to create user: %s", e)
            flash("Registration failed. Please try again.", "error")

    return render_template("register.html", form={})


# ─── Logout ───────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    name = session.get("full_name", "")
    session.clear()
    flash(f"Goodbye, {name}! You have been logged out.", "success")
    return redirect(url_for("auth.login_page"))


# ─── Helper ───────────────────────────────────────────────────────────────────

def _redirect_by_role(role: str):
    if role == "faculty":
        return redirect(url_for("faculty.dashboard"))
    elif role == "student":
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("admin.dashboard"))
