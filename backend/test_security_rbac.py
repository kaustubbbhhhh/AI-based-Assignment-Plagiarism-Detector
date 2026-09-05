import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_URL"] = "sqlite:///./plagiarism.db"

from fastapi.testclient import TestClient
from main import app
from core.database import Base, SessionLocal, engine
from core.security import hash_password, create_access_token
from models.user import User, UserRole
from models.submission import Submission, SubmissionStatus
from models.report import Report, ContentLabel
from api.submissions import _sanitize_filename


client = TestClient(app)


def _auth_header(user_id: int, role: str):
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"******"}


def test_rbac_and_filename_sanitization():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    suffix = uuid.uuid4().hex[:8]

    student_a = User(
        name="Student A",
        email=f"student-a-{suffix}@test.edu",
        hashed_password=hash_password("pass123"),
        role=UserRole.student,
        section="IT-A",
    )
    student_b = User(
        name="Student B",
        email=f"student-b-{suffix}@test.edu",
        hashed_password=hash_password("pass123"),
        role=UserRole.student,
        section="IT-B",
    )
    teacher_assigned = User(
        name="Teacher Assigned",
        email=f"teacher-assigned-{suffix}@test.edu",
        hashed_password=hash_password("pass123"),
        role=UserRole.teacher,
        subjects_sections=[{"subject": "Compiler Design", "section": "IT-A"}],
    )
    teacher_unassigned = User(
        name="Teacher Unassigned",
        email=f"teacher-unassigned-{suffix}@test.edu",
        hashed_password=hash_password("pass123"),
        role=UserRole.teacher,
        subjects_sections=[{"subject": "Operating Systems", "section": "IT-C"}],
    )
    hod_user = User(
        name="HOD",
        email=f"hod-{suffix}@test.edu",
        hashed_password=hash_password("pass123"),
        role=UserRole.hod,
    )

    db.add_all([student_a, student_b, teacher_assigned, teacher_unassigned, hod_user])
    db.commit()
    db.refresh(student_a)
    db.refresh(student_b)
    db.refresh(teacher_assigned)
    db.refresh(teacher_unassigned)
    db.refresh(hod_user)

    submission = Submission(
        student_id=student_a.id,
        subject="Compiler Design",
        assignment_title="Assignment 1",
        filename="assignment.txt",
        filepath="uploads/assignment.txt",
        status=SubmissionStatus.completed,
        is_locked=False,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    report = Report(
        submission_id=submission.id,
        ai_score=20.0,
        plagiarism_score=10.0,
        ocr_score=99.0,
        ocr_status="Accepted",
        label=ContentLabel.original,
        processed_text="Sample processed text for security tests.",
        word_count=6,
        sentence_count=1,
    )
    db.add(report)
    db.commit()

    student_a_h = _auth_header(student_a.id, "student")
    student_b_h = _auth_header(student_b.id, "student")
    teacher_ok_h = _auth_header(teacher_assigned.id, "teacher")
    teacher_no_h = _auth_header(teacher_unassigned.id, "teacher")
    hod_h = _auth_header(hod_user.id, "hod")

    res = client.get(f"/api/status/{submission.id}", headers=student_a_h)
    assert res.status_code == 200, res.text
    res = client.get(f"/api/report/{submission.id}", headers=student_a_h)
    assert res.status_code == 200, res.text

    assert client.get(f"/api/status/{submission.id}", headers=student_b_h).status_code == 403
    assert client.get(f"/api/report/{submission.id}", headers=student_b_h).status_code == 403

    assert client.get(f"/api/status/{submission.id}", headers=teacher_ok_h).status_code == 200
    assert client.get(f"/api/report/{submission.id}", headers=teacher_ok_h).status_code == 200
    assert client.get(
        "/api/reports/section/IT-A?subject=Compiler%20Design",
        headers=teacher_ok_h,
    ).status_code == 200

    assert client.get(f"/api/status/{submission.id}", headers=teacher_no_h).status_code == 403
    assert client.get(f"/api/report/{submission.id}", headers=teacher_no_h).status_code == 403
    assert client.get(
        "/api/reports/section/IT-A?subject=Compiler%20Design",
        headers=teacher_no_h,
    ).status_code == 403

    assert client.get(f"/api/status/{submission.id}", headers=hod_h).status_code == 200
    assert client.get(f"/api/report/{submission.id}", headers=hod_h).status_code == 200

    assert _sanitize_filename("../../dangerous?.pdf") == "dangerous_.pdf"
    assert _sanitize_filename("..\\evil<>.txt") == "evil__.txt"
    assert _sanitize_filename("") == ""

    db.delete(report)
    db.delete(submission)
    db.delete(student_a)
    db.delete(student_b)
    db.delete(teacher_assigned)
    db.delete(teacher_unassigned)
    db.delete(hod_user)
    db.commit()
    db.close()


if __name__ == "__main__":
    test_rbac_and_filename_sanitization()
    print("RBAC and filename sanitization tests passed.")
