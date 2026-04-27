"""
Configuration – reads from environment variables.
Set these in your EC2 instance or .env file (never hard-code credentials).
"""

import os


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE  = "Lax"

    # AWS Region
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

    # DynamoDB Table Names
    DYNAMO_USERS_TABLE       = os.environ.get("DYNAMO_USERS_TABLE",       "sas_users")
    DYNAMO_COURSES_TABLE     = os.environ.get("DYNAMO_COURSES_TABLE",     "sas_courses")
    DYNAMO_ATTENDANCE_TABLE  = os.environ.get("DYNAMO_ATTENDANCE_TABLE",  "sas_attendance")
    DYNAMO_ENROLLMENT_TABLE  = os.environ.get("DYNAMO_ENROLLMENT_TABLE",  "sas_enrollment")

    # SNS
    SNS_TOPIC_ARN            = os.environ.get("SNS_TOPIC_ARN", "")

    # Attendance threshold (%)
    ATTENDANCE_THRESHOLD     = int(os.environ.get("ATTENDANCE_THRESHOLD", 75))
