"""
Database helpers – all DynamoDB interactions live here.
"""

import uuid
import logging
from datetime import date, datetime
from typing import Optional, List

from boto3.dynamodb.conditions import Key, Attr
from aws_clients import table
from flask import current_app

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# USER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def create_user(username: str, password_hash: str, role: str,
                email: str, full_name: str) -> dict:
    """Create a new user (student or faculty or admin)."""
    t = table("DYNAMO_USERS_TABLE")
    user_id = str(uuid.uuid4())
    item = {
        "user_id":       user_id,
        "username":      username,
        "password_hash": password_hash,
        "role":          role,          # 'student' | 'faculty' | 'admin'
        "email":         email,
        "full_name":     full_name,
        "created_at":    datetime.utcnow().isoformat(),
        "is_active":     True,
    }
    t.put_item(Item=item)
    logger.info("Created user %s (%s)", username, role)
    return item


def get_user_by_username(username: str) -> Optional[dict]:
    """Scan users table for a matching username (username is unique)."""
    t = table("DYNAMO_USERS_TABLE")
    resp = t.scan(FilterExpression=Attr("username").eq(username))
    items = resp.get("Items", [])
    return items[0] if items else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    t = table("DYNAMO_USERS_TABLE")
    resp = t.get_item(Key={"user_id": user_id})
    return resp.get("Item")


def list_users_by_role(role: str) -> List[dict]:
    t = table("DYNAMO_USERS_TABLE")
    resp = t.scan(FilterExpression=Attr("role").eq(role))
    return resp.get("Items", [])


# ══════════════════════════════════════════════════════════════════════════════
# COURSE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def create_course(course_name: str, course_code: str, faculty_id: str) -> dict:
    t = table("DYNAMO_COURSES_TABLE")
    course_id = str(uuid.uuid4())
    item = {
        "course_id":   course_id,
        "course_name": course_name,
        "course_code": course_code,
        "faculty_id":  faculty_id,
        "created_at":  datetime.utcnow().isoformat(),
    }
    t.put_item(Item=item)
    return item


def get_course(course_id: str) -> Optional[dict]:
    t = table("DYNAMO_COURSES_TABLE")
    resp = t.get_item(Key={"course_id": course_id})
    return resp.get("Item")


def list_courses_by_faculty(faculty_id: str) -> List[dict]:
    t = table("DYNAMO_COURSES_TABLE")
    resp = t.scan(FilterExpression=Attr("faculty_id").eq(faculty_id))
    return resp.get("Items", [])


def list_all_courses() -> List[dict]:
    t = table("DYNAMO_COURSES_TABLE")
    resp = t.scan()
    return resp.get("Items", [])


# ══════════════════════════════════════════════════════════════════════════════
# ENROLLMENT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def enroll_student(course_id: str, student_id: str) -> dict:
    t = table("DYNAMO_ENROLLMENT_TABLE")
    item = {
        "enrollment_id": str(uuid.uuid4()),
        "course_id":     course_id,
        "student_id":    student_id,
        "enrolled_at":   datetime.utcnow().isoformat(),
    }
    t.put_item(Item=item)
    return item


def get_students_in_course(course_id: str) -> List[dict]:
    t = table("DYNAMO_ENROLLMENT_TABLE")
    resp = t.scan(FilterExpression=Attr("course_id").eq(course_id))
    return resp.get("Items", [])


def get_courses_for_student(student_id: str) -> List[dict]:
    t = table("DYNAMO_ENROLLMENT_TABLE")
    resp = t.scan(FilterExpression=Attr("student_id").eq(student_id))
    return resp.get("Items", [])


# ══════════════════════════════════════════════════════════════════════════════
# ATTENDANCE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def mark_attendance(course_id: str, student_id: str,
                    status: str, date_str: Optional[str] = None) -> dict:
    """
    Mark a single attendance record.
    status: 'present' | 'absent'
    date_str: YYYY-MM-DD (default: today UTC)
    """
    t = table("DYNAMO_ATTENDANCE_TABLE")
    if date_str is None:
        date_str = date.today().isoformat()

    record_id = str(uuid.uuid4())
    item = {
        "record_id":  record_id,
        "course_id":  course_id,
        "student_id": student_id,
        "date":       date_str,
        "status":     status.lower(),
        "marked_at":  datetime.utcnow().isoformat(),
    }
    t.put_item(Item=item)
    return item


def get_attendance_for_student_course(student_id: str, course_id: str) -> List[dict]:
    t = table("DYNAMO_ATTENDANCE_TABLE")
    resp = t.scan(
        FilterExpression=(
            Attr("student_id").eq(student_id) & Attr("course_id").eq(course_id)
        )
    )
    return resp.get("Items", [])


def get_attendance_for_course_date(course_id: str, date_str: str) -> List[dict]:
    t = table("DYNAMO_ATTENDANCE_TABLE")
    resp = t.scan(
        FilterExpression=(
            Attr("course_id").eq(course_id) & Attr("date").eq(date_str)
        )
    )
    return resp.get("Items", [])


# ══════════════════════════════════════════════════════════════════════════════
# ATTENDANCE PERCENTAGE
# ══════════════════════════════════════════════════════════════════════════════

def calculate_attendance_percentage(student_id: str, course_id: str) -> float:
    """Returns attendance percentage 0-100 for a student in a course."""
    records = get_attendance_for_student_course(student_id, course_id)
    if not records:
        return 0.0
    total   = len(records)
    present = sum(1 for r in records if r.get("status") == "present")
    return round((present / total) * 100, 2)
