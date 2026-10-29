"""
Direct Database Seed Script for Demo Users and Admin.

Inserts initial users directly into the database so the server does not need to be running.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.security import hash_password
from models.user import User, UserRole
from models.subject import Subject, SubjectStatus
from models.submission import Submission
from models.session import Session
from models.report import Report

demo_users = [
    {
        "name": "Kaustubh Raj", "email": "student@demo.edu", "password": "Password123",
        "role": UserRole.student, "phone": "9876543210", "enrollment_no": "12114803124",
        "father_phone": "9876500001", "mother_phone": "9876500002",
        "section": "4I1", "branch": "IT", "session": "2024-2028", "semester": 4,
    },
    {
        "name": "Ajay Kaushik", "email": "teacher@demo.edu", "password": "Password123",
        "role": UserRole.teacher, "phone": "9876543211", "teacher_id": "FAC-2024-01",
        "branch": "IT", "section": "4I1",
        "subjects_sections": [
            {"subject": "Database Management Systems", "section": "IT-4I1"},
            {"subject": "Programming in Java", "section": "IT-4I2"}
        ]
    },
    {
        "name": "Amita Goel", "email": "hod@demo.edu", "password": "Password123",
        "role": UserRole.hod, "phone": "9876543212", "hod_id": "HOD-IT-01",
        "department": "IT", "branch": "IT"
    },
    {
        "name": "System Admin", "email": "admin@plagiarismai.edu", "password": "Admin@1234",
        "role": UserRole.admin, "phone": "9876543213"
    }
]

demo_subjects = [
    {"subject_code": "CIC-210", "subject_name": "Database Management Systems", "branch": "IT", "semester": 4},
    {"subject_code": "CIC-212", "subject_name": "Theory of Computation", "branch": "IT", "semester": 4},
    {"subject_code": "BAS-204", "subject_name": "Probability, Statistics and Linear Programming", "branch": "IT", "semester": 4},
    {"subject_code": "ECC-216", "subject_name": "Circuits and Systems", "branch": "IT", "semester": 4},
    {"subject_code": "CIC-218", "subject_name": "Programming in Java", "branch": "IT", "semester": 4},
    {"subject_code": "CS-301", "subject_name": "Operating Systems", "branch": "CSE", "semester": 5},
    {"subject_code": "CS-303", "subject_name": "Computer Networks", "branch": "CSE", "semester": 5},
]

def seed():
    print("=" * 60)
    print("Seeding Initial Users and Subjects into Database")
    print("=" * 60)
    db = SessionLocal()
    try:
        # Seed users
        for u_data in demo_users:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if existing:
                print(f"  [EXISTS] User: {u_data['email']} ({u_data['role'].value})")
            else:
                user = User(
                    name=u_data["name"],
                    email=u_data["email"],
                    hashed_password=hash_password(u_data["password"]),
                    role=u_data["role"],
                    phone=u_data.get("phone"),
                    is_verified=True,
                    must_change_password=False,
                    enrollment_no=u_data.get("enrollment_no"),
                    father_phone=u_data.get("father_phone"),
                    mother_phone=u_data.get("mother_phone"),
                    section=u_data.get("section"),
                    branch=u_data.get("branch"),
                    session=u_data.get("session"),
                    semester=u_data.get("semester"),
                    teacher_id=u_data.get("teacher_id"),
                    subjects_sections=u_data.get("subjects_sections"),
                    hod_id=u_data.get("hod_id"),
                    department=u_data.get("department"),
                )
                db.add(user)
                db.commit()
                print(f"  [CREATED] User: {u_data['email']} ({u_data['role'].value})")

        # Seed subjects
        for s_data in demo_subjects:
            existing_sub = db.query(Subject).filter(
                Subject.subject_code == s_data["subject_code"],
                Subject.branch == s_data["branch"],
                Subject.semester == s_data["semester"],
            ).first()
            if existing_sub:
                print(f"  [EXISTS] Subject: {s_data['subject_code']} - {s_data['subject_name']}")
            else:
                sub = Subject(
                    subject_code=s_data["subject_code"],
                    subject_name=s_data["subject_name"],
                    branch=s_data["branch"],
                    semester=s_data["semester"],
                    status=SubjectStatus.active,
                )
                db.add(sub)
                db.commit()
                print(f"  [CREATED] Subject: {s_data['subject_code']} - {s_data['subject_name']}")

        print("=" * 60)
        print("Seeding Complete!")
        print("  Admin:   admin@plagiarismai.edu / Admin@1234")
        print("  Student: student@demo.edu / Password123")
        print("  Teacher: teacher@demo.edu / Password123")
        print("  HOD:     hod@demo.edu / Password123")
        print("=" * 60)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
