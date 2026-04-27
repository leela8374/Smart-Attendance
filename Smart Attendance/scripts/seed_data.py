"""
scripts/seed_data.py
Seeds the database with:
  - 1 admin user
  - 1 faculty user
  - 3 student users
  - 2 courses
  - Enrolls all students in both courses
Run AFTER setup_dynamo.py:
    python scripts/seed_data.py
"""

import sys, os
import hashlib

# Allow importing project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Bootstrap Flask app so AWS clients initialise correctly
from app import create_app

app = create_app()

with app.app_context():
    from db import create_user, create_course, enroll_student

    def pw(p): return hashlib.sha256(p.encode()).hexdigest()

    print("Creating users...")
    admin   = create_user("admin",   pw("Admin@123"),   "admin",   "admin@college.edu",   "System Admin")
    faculty = create_user("faculty1",pw("Faculty@123"), "faculty", "faculty1@college.edu","Dr. Priya Sharma")
    s1      = create_user("student1",pw("Student@123"), "student", "student1@college.edu","Ravi Kumar")
    s2      = create_user("student2",pw("Student@123"), "student", "student2@college.edu","Ananya Singh")
    s3      = create_user("student3",pw("Student@123"), "student", "student3@college.edu","Kiran Patel")

    print("Creating courses...")
    c1 = create_course("Data Structures",    "CS301", faculty["user_id"])
    c2 = create_course("Operating Systems",  "CS401", faculty["user_id"])

    print("Enrolling students...")
    for s in [s1, s2, s3]:
        enroll_student(c1["course_id"], s["user_id"])
        enroll_student(c2["course_id"], s["user_id"])

    print("\n✅ Seed complete!")
    print("┌─────────────┬──────────────┬──────────────┐")
    print("│ Role        │ Username     │ Password     │")
    print("├─────────────┼──────────────┼──────────────┤")
    print("│ Admin       │ admin        │ Admin@123    │")
    print("│ Faculty     │ faculty1     │ Faculty@123  │")
    print("│ Student 1   │ student1     │ Student@123  │")
    print("│ Student 2   │ student2     │ Student@123  │")
    print("│ Student 3   │ student3     │ Student@123  │")
    print("└─────────────┴──────────────┴──────────────┘")
