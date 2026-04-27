"""
Admin routes – manage users, courses, enrollments.
"""

import hashlib
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template, flash,
)
from db import (
    create_user, list_users_by_role, create_course,
    list_all_courses, enroll_student, get_user_by_id,
)

admin_bp = Blueprint("admin", __name__)


def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()


def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Access denied.", "error")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard")
@require_admin
def dashboard():
    students = list_users_by_role("student")
    faculty  = list_users_by_role("faculty")
    courses  = list_all_courses()
    return render_template(
        "admin_dashboard.html",
        students=students,
        faculty=faculty,
        courses=courses,
        full_name=session["full_name"],
    )


# ─── Create User ─────────────────────────────────────────────────────────────

@admin_bp.route("/create-user", methods=["GET", "POST"])
@require_admin
def create_user_page():
    if request.method == "POST":
        try:
            create_user(
                username      = request.form["username"].strip(),
                password_hash = hash_password(request.form["password"]),
                role          = request.form["role"],
                email         = request.form["email"].strip(),
                full_name     = request.form["full_name"].strip(),
            )
            flash("User created successfully.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_create_user.html", full_name=session["full_name"])


# ─── Create Course ───────────────────────────────────────────────────────────

@admin_bp.route("/create-course", methods=["GET", "POST"])
@require_admin
def create_course_page():
    faculty_list = list_users_by_role("faculty")
    if request.method == "POST":
        try:
            create_course(
                course_name = request.form["course_name"].strip(),
                course_code = request.form["course_code"].strip(),
                faculty_id  = request.form["faculty_id"],
            )
            flash("Course created successfully.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_create_course.html",
                           faculty_list=faculty_list,
                           full_name=session["full_name"])


# ─── Enroll Student ──────────────────────────────────────────────────────────

@admin_bp.route("/enroll", methods=["GET", "POST"])
@require_admin
def enroll_page():
    students = list_users_by_role("student")
    courses  = list_all_courses()
    if request.method == "POST":
        try:
            enroll_student(
                course_id  = request.form["course_id"],
                student_id = request.form["student_id"],
            )
            flash("Student enrolled successfully.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_enroll.html",
                           students=students,
                           courses=courses,
                           full_name=session["full_name"])
