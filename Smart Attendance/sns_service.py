"""
AWS SNS Alert Service
Sends email alerts when attendance drops below threshold.
"""

import logging
from aws_clients import get_sns
from flask import current_app

logger = logging.getLogger(__name__)


def send_low_attendance_alert(
    student_name: str,
    student_email: str,
    course_name: str,
    attendance_pct: float,
    threshold: int,
) -> bool:
    """
    Publish a low-attendance alert to the configured SNS topic.
    Returns True on success.
    """
    sns       = get_sns()
    topic_arn = current_app.config["SNS_TOPIC_ARN"]

    subject = f"⚠️ Low Attendance Alert – {student_name}"
    message = (
        f"Dear {student_name},\n\n"
        f"Your attendance in [{course_name}] has dropped to "
        f"{attendance_pct:.1f}%, which is below the required "
        f"{threshold}% minimum.\n\n"
        f"Please attend classes regularly to avoid academic penalties.\n\n"
        f"– Smart Attendance System"
    )

    try:
        response = sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message,
            MessageAttributes={
                "student_email": {
                    "DataType":    "String",
                    "StringValue": student_email,
                }
            },
        )
        logger.info(
            "SNS alert sent for %s | Course: %s | Pct: %.1f%% | MessageId: %s",
            student_name, course_name, attendance_pct,
            response["MessageId"],
        )
        return True
    except Exception as exc:
        logger.error("Failed to send SNS alert: %s", exc)
        return False


def send_bulk_alerts(alert_list: list) -> dict:
    """
    alert_list: list of dicts with keys
        {student_name, student_email, course_name, attendance_pct}
    Returns {"sent": N, "failed": M}
    """
    threshold = current_app.config["ATTENDANCE_THRESHOLD"]
    sent = failed = 0
    for a in alert_list:
        ok = send_low_attendance_alert(
            student_name   = a["student_name"],
            student_email  = a["student_email"],
            course_name    = a["course_name"],
            attendance_pct = a["attendance_pct"],
            threshold      = threshold,
        )
        if ok:
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed}
