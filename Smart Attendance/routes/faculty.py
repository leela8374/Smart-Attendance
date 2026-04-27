"""
Faculty routes – mark attendance, view reports, trigger alerts.
"""

from datetime import date
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template, flash, jsonify,
)
from db import (
    list_courses_by_faculty, get_students_in_course, get_user_by_id,
    mark_attendance, get_attendance_for_course_date,
    calculate_attendance_percentage, get_course,
    get_attendance_for_student_course,
)
from sns_service import send_bulk_alerts
from flask import current_app

faculty_bp = Blueprint("faculty", __name__)


def require_faculty(f):
    """Decorator: ensure session has faculty role."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "faculty":
            flash("Access denied.", "error")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ───────────────────────────────────────────────────────────────

@faculty_bp.route("/dashboard")
@require_faculty
def dashboard():
    faculty_id = session["user_id"]
    courses = list_courses_by_faculty(faculty_id)
    return render_template("faculty_dashboard.html",
                           courses=courses,
                           full_name=session["full_name"])


# ─── Mark Attendance ─────────────────────────────────────────────────────────

@faculty_bp.route("/mark-attendance/<course_id>", methods=["GET", "POST"])
@require_faculty
def mark_attendance_page(course_id):
    course = get_course(course_id)
    if not course or course["faculty_id"] != session["user_id"]:
        flash("Course not found.", "error")
        return redirect(url_for("faculty.dashboard"))

    enrollments = get_students_in_course(course_id)
    students = []
    for enr in enrollments:
        u = get_user_by_id(enr["student_id"])
        if u:
            students.append(u)

    today = date.today().isoformat()

    if request.method == "POST":
        date_str   = request.form.get("date", today)
        statuses   = request.form.to_dict()  # student_id -> 'present'/'absent'
        threshold  = current_app.config["ATTENDANCE_THRESHOLD"]
        alerts_to_send = []

        for student in students:
            sid    = student["user_id"]
            status = statuses.get(f"status_{sid}", "absent")
            mark_attendance(course_id, sid, status, date_str)

            # Check attendance percentage after marking
            pct = calculate_attendance_percentage(sid, course_id)
            if pct < threshold:
                alerts_to_send.append({
                    "student_name":   student["full_name"],
                    "student_email":  student["email"],
                    "course_name":    course["course_name"],
                    "attendance_pct": pct,
                })

        if alerts_to_send:
            result = send_bulk_alerts(alerts_to_send)
            flash(
                f"Attendance marked. SNS alerts sent: {result['sent']}, "
                f"failed: {result['failed']}.",
                "warning",
            )
        else:
            flash("Attendance marked successfully. All students above threshold.", "success")

        return redirect(url_for("faculty.attendance_report", course_id=course_id))

    # Check already marked today
    already_marked = {
        r["student_id"]: r["status"]
        for r in get_attendance_for_course_date(course_id, today)
    }

    return render_template(
        "mark_attendance.html",
        course=course,
        students=students,
        today=today,
        already_marked=already_marked,
        full_name=session["full_name"],
    )


# ─── Attendance Report ───────────────────────────────────────────────────────

@faculty_bp.route("/report/<course_id>")
@require_faculty
def attendance_report(course_id):
    course = get_course(course_id)
    if not course or course["faculty_id"] != session["user_id"]:
        flash("Course not found.", "error")
        return redirect(url_for("faculty.dashboard"))

    threshold    = current_app.config["ATTENDANCE_THRESHOLD"]
    enrollments  = get_students_in_course(course_id)
    report_rows  = []

    for enr in enrollments:
        u = get_user_by_id(enr["student_id"])
        if not u:
            continue
        records = get_attendance_for_student_course(enr["student_id"], course_id)
        total   = len(records)
        present = sum(1 for r in records if r.get("status") == "present")
        pct     = round((present / total * 100), 2) if total else 0.0
        report_rows.append({
            "student_name":  u["full_name"],
            "student_email": u["email"],
            "total":         total,
            "present":       present,
            "absent":        total - present,
            "percentage":    pct,
            "below_threshold": pct < threshold,
        })

    return render_template(
        "attendance_report.html",
        course=course,
        rows=report_rows,
        threshold=threshold,
        full_name=session["full_name"],
    )


# ─── Manual Alert Trigger (AJAX) ─────────────────────────────────────────────

@faculty_bp.route("/send-alerts/<course_id>", methods=["POST"])
@require_faculty
def send_alerts(course_id):
    course = get_course(course_id)
    threshold   = current_app.config["ATTENDANCE_THRESHOLD"]
    enrollments = get_students_in_course(course_id)
    alerts_to_send = []

    for enr in enrollments:
        u = get_user_by_id(enr["student_id"])
        if not u:
            continue
        pct = calculate_attendance_percentage(enr["student_id"], course_id)
        if pct < threshold:
            alerts_to_send.append({
                "student_name":   u["full_name"],
                "student_email":  u["email"],
                "course_name":    course["course_name"],
                "attendance_pct": pct,
            })

    result = send_bulk_alerts(alerts_to_send)
    return jsonify({"status": "ok", **result})
