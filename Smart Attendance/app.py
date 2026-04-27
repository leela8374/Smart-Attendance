"""
Smart Attendance Alert System
Main Flask Application Entry Point
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env BEFORE config reads os.environ

from flask import Flask
from config import Config
from routes.auth import auth_bp
from routes.faculty import faculty_bp
from routes.student import student_bp
from routes.admin import admin_bp
import logging

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(auth_bp,    url_prefix="/auth")
    app.register_blueprint(faculty_bp, url_prefix="/faculty")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(admin_bp,   url_prefix="/admin")

    # Root redirect
    from flask import redirect, url_for, jsonify
    from aws_clients import check_dynamodb_connection
    import os

    @app.route("/")
    def index():
        return redirect(url_for("auth.login_page"))

    @app.route("/health")
    def health():
        """
        Health-check endpoint — open in browser to diagnose AWS issues.
        http://<ec2-ip>:5000/health
        """
        status = check_dynamodb_connection()
        status["env"] = {
            "AWS_REGION":              os.environ.get("AWS_REGION",              "NOT SET"),
            "DYNAMO_USERS_TABLE":      os.environ.get("DYNAMO_USERS_TABLE",      "NOT SET"),
            "DYNAMO_COURSES_TABLE":    os.environ.get("DYNAMO_COURSES_TABLE",    "NOT SET"),
            "DYNAMO_ATTENDANCE_TABLE": os.environ.get("DYNAMO_ATTENDANCE_TABLE", "NOT SET"),
            "DYNAMO_ENROLLMENT_TABLE": os.environ.get("DYNAMO_ENROLLMENT_TABLE", "NOT SET"),
            "SNS_TOPIC_ARN":           os.environ.get("SNS_TOPIC_ARN",           "NOT SET"),
        }
        return jsonify(status), 200 if status["ok"] else 503

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
