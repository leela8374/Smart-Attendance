"""
Student routes – view own attendance per course.
"""

from flask import Blueprint, session, redirect, url_for, render_template, flash
from db import (
    get_courses_for_student, get_course, get_user_by_id,
    calculate_attendance_percentage, get_attendance_for_student_course,
)
from flask import current_app

student_bp = Blueprint("student", __name__)


def require_student(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "student":
            flash("Access denied.", "error")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


@student_bp.route("/dashboard")
@require_student
def dashboard():
    student_id  = session["user_id"]
    threshold   = current_app.config["ATTENDANCE_THRESHOLD"]
    enrollments = get_courses_for_student(student_id)
    course_data = []

    for enr in enrollments:
        course = get_course(enr["course_id"])
        if not course:
            continue
        pct = calculate_attendance_percentage(student_id, enr["course_id"])
        course_data.append({
            "course_id":     course["course_id"],
            "course_name":   course["course_name"],
            "course_code":   course["course_code"],
            "percentage":    pct,
            "below_threshold": pct < threshold,
        })

    return render_template(
        "student_dashboard.html",
        courses=course_data,
        threshold=threshold,
        full_name=session["full_name"],
    )


@student_bp.route("/attendance/<course_id>")
@require_student
def view_attendance(course_id):
    student_id = session["user_id"]
    course     = get_course(course_id)
    threshold  = current_app.config["ATTENDANCE_THRESHOLD"]

    records = get_attendance_for_student_course(student_id, course_id)
    records.sort(key=lambda r: r.get("date", ""))

    pct = calculate_attendance_percentage(student_id, course_id)

    return render_template(
        "student_attendance.html",
        course=course,
        records=records,
        percentage=pct,
        threshold=threshold,
        full_name=session["full_name"],
    )
