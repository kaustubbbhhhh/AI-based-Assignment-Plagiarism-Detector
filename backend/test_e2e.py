"""Complete E2E Test Suite for PlagiarismAI System."""
import requests
import json
import os

BASE = "http://127.0.0.1:8001"
PASS = "pass123"

def section(title):
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")

def check(label, condition, detail=""):
    symbol = "PASS" if condition else "FAIL"
    print(f"  [{symbol}] {label}" + (f" — {detail}" if detail else ""))
    return condition

def test():
    print("=" * 60)
    print("  PlagiarismAI — Complete System Test Suite")
    print("=" * 60)
    all_pass = True

    # ── 1. Health Check ───────────────────────────────────────
    section("1. Health Check")
    try:
        r = requests.get(f"{BASE}/api/health")
        all_pass &= check("API Health", r.status_code == 200, r.json().get("status"))
    except requests.exceptions.ConnectionError:
        print("  [FAIL] Could not connect to the backend server. Is it running?")
        return

    # ── 2. Registration ───────────────────────────────────────
    section("2. Registration (New Student)")
    r = requests.post(f"{BASE}/api/auth/register", json={
        "name": "Test Student", "email": "teststudent@e2e.edu", "password": PASS,
        "role": "student", "phone": "1234567890", "enrollment_no": "ENR-E2E-001",
        "father_phone": "1111111111", "mother_phone": "2222222222",
        "section": "IT-A", "branch": "IT", "session": "2024-2028"
    })
    all_pass &= check("Student Registration", r.status_code == 201, f"id={r.json().get('id')}")

    section("2b. Registration (Duplicate Check)")
    r2 = requests.post(f"{BASE}/api/auth/register", json={
        "name": "Test Student", "email": "teststudent@e2e.edu", "password": PASS,
        "role": "student"
    })
    all_pass &= check("Duplicate Email Rejected", r2.status_code == 409, r2.json().get("detail","")[:50])

    # ── 3. Login (All Roles) ──────────────────────────────────
    section("3. Login (All Roles)")
    
    # Student
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "teststudent@e2e.edu", "password": PASS})
    all_pass &= check("Student Login", r.status_code == 200, f"role={r.json().get('user',{}).get('role')}")
    student_token = r.json().get("access_token", "")
    student_headers = {"Authorization": f"Bearer {student_token}"}
    
    # Teacher
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "teacher@demo.edu", "password": PASS})
    all_pass &= check("Teacher Login", r.status_code == 200, f"role={r.json().get('user',{}).get('role')}")
    teacher_token = r.json().get("access_token", "")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # HOD
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "hod@demo.edu", "password": PASS})
    all_pass &= check("HOD Login", r.status_code == 200, f"role={r.json().get('user',{}).get('role')}")
    hod_token = r.json().get("access_token", "")
    hod_headers = {"Authorization": f"Bearer {hod_token}"}

    # Wrong password
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "teststudent@e2e.edu", "password": "wrong"})
    all_pass &= check("Wrong Password Rejected", r.status_code == 401)

    # ── 4. File Upload + Processing ───────────────────────────
    section("4. File Upload + AI/Plagiarism Processing")
    
    test_text = (
        "Artificial intelligence has fundamentally transformed the landscape of modern computing. "
        "Machine learning algorithms can identify complex patterns in massive datasets with remarkable accuracy. "
        "Deep neural networks, which are inspired by the architecture of the human brain, "
        "form the foundational backbone of contemporary deep learning methodologies. "
        "Convolutional neural networks have demonstrated exceptional performance in image recognition. "
        "Natural language processing enables computational systems to interpret human text effectively. "
        "Reinforcement learning allows agents to make optimal decisions through trial and error. "
        "Transfer learning significantly reduces the computational resources needed for training new models."
    )
    with open("_test_e2e_file.txt", "w") as f:
        f.write(test_text)

    files = {"file": ("test_e2e_assignment.txt", open("_test_e2e_file.txt", "rb"), "text/plain")}
    data = {"subject": "Introduction to Artificial Intelligence"}
    r = requests.post(f"{BASE}/api/submit", files=files, data=data, headers=student_headers)
    all_pass &= check("File Upload", r.status_code == 202, r.json().get("message","")[:50])
    sub_id = r.json().get("submission_id")

    # ── 5. Status Check ───────────────────────────────────────
    section("5. Submission Status")
    r = requests.get(f"{BASE}/api/status/{sub_id}", headers=student_headers)
    status_data = r.json()
    all_pass &= check("Status Endpoint", r.status_code == 200, f"status={status_data.get('status')}")
    all_pass &= check("AI Score Present", status_data.get("ai_score") is not None, f"ai_score={status_data.get('ai_score')}%")
    all_pass &= check("Plagiarism Score", status_data.get("plagiarism_score") is not None, f"plag_score={status_data.get('plagiarism_score')}%")
    all_pass &= check("Label Assigned", status_data.get("label") is not None, f"label={status_data.get('label')}")

    # ── 6. Full Report ────────────────────────────────────────
    section("6. Full Report Retrieval")
    r = requests.get(f"{BASE}/api/report/{sub_id}", headers=student_headers)
    all_pass &= check("Report Endpoint", r.status_code == 200)
    report = r.json()
    all_pass &= check("Word Count Present", report.get("word_count") is not None, f"words={report.get('word_count')}")
    all_pass &= check("Text Stored", len(report.get("processed_text","")) > 50, f"chars={len(report.get('processed_text',''))}")

    # ── 7. Teacher Section Reports ────────────────────────────
    section("7. Teacher — Section Reports")
    r = requests.get(f"{BASE}/api/reports/section/IT-A", headers=teacher_headers)
    r_json = r.json() if r.status_code == 200 else []
    all_pass &= check("Section Reports", r.status_code == 200, f"count={len(r_json)}")
    if r_json:
        rep = r_json[0]
        all_pass &= check("Has Student Name", rep.get("student_name") is not None, rep.get("student_name",""))
        all_pass &= check("Has Section Field", rep.get("section") is not None, rep.get("section",""))

    # ── 7b. Teacher Subject/Section Mappings ──────────────────
    section("7b. Teacher — Manage Subjects/Sections Mappings")
    new_mappings = [
        {"subject": "Compiler Design", "section": "IT-A"},
        {"subject": "Operating Systems", "section": "IT-B"}
    ]
    r_put = requests.put(f"{BASE}/api/auth/teacher/subjects", json=new_mappings, headers=teacher_headers)
    all_pass &= check("Update Subjects Mappings", r_put.status_code == 200, f"mappings_count={len(r_put.json().get('subjects_sections', []))}")
    if r_put.status_code == 200:
        saved_mappings = r_put.json().get('subjects_sections', [])
        match = any(m["subject"] == "Compiler Design" and m["section"] == "IT-A" for m in saved_mappings)
        all_pass &= check("Correct Mapping Saved", match)

    # ── 8. HOD Batch Reports ──────────────────────────────────
    section("8. HOD — Batch Reports")
    r = requests.get(f"{BASE}/api/reports/batch", headers=hod_headers)
    batch_json = r.json() if r.status_code == 200 else []
    all_pass &= check("Batch Reports", r.status_code == 200, f"count={len(batch_json)}")
    if batch_json:
        all_pass &= check("Contains AI/Plagiarism Scores", "ai_score" in batch_json[0])

    # ── 9. Access Control ─────────────────────────────────────
    section("9. Access Control (RBAC)")
    r = requests.get(f"{BASE}/api/reports/section/IT-A", headers=student_headers)
    all_pass &= check("Student Cannot See Section Reports", r.status_code == 403)

    r = requests.get(f"{BASE}/api/reports/batch", headers=teacher_headers)
    all_pass &= check("Teacher Cannot See Batch Reports", r.status_code == 403)

    r = requests.get(f"{BASE}/api/status/{sub_id}")  # no token
    all_pass &= check("Unauthenticated Access Blocked", r.status_code == 401)

    # ── 10. Second Upload for Plagiarism Comparison ───────────
    section("10. Plagiarism Cross-Check (2nd Upload)")
    similar_text = (
        "Artificial intelligence has fundamentally changed the landscape of modern computing. "
        "Machine learning models identify complex patterns in massive datasets with high accuracy. "
        "Deep neural networks form the backbone of deep learning methodologies. "
        "CNNs have demonstrated excellent performance in image recognition tasks."
    )
    with open("_test_e2e_file2.txt", "w") as f:
        f.write(similar_text)

    files2 = {"file": ("plagiarism_test.txt", open("_test_e2e_file2.txt", "rb"), "text/plain")}
    r = requests.post(f"{BASE}/api/submit", files=files2, data=data, headers=student_headers)
    all_pass &= check("2nd File Upload", r.status_code == 202)
    sub2_id = r.json().get("submission_id")

    r = requests.get(f"{BASE}/api/status/{sub2_id}", headers=student_headers)
    s2 = r.json()
    plag_score = s2.get("plagiarism_score") or 0
    all_pass &= check("Plagiarism Detected", plag_score > 0, f"plag={plag_score}%")

    # Cleanup
    try:
        os.remove("_test_e2e_file.txt")
        os.remove("_test_e2e_file2.txt")
    except:
        pass

    # ── FINAL RESULT ──────────────────────────────────────────
    print("\n" + "=" * 60)
    if all_pass:
        print("  ALL TESTS PASSED!")
    else:
        print("  SOME TESTS FAILED — review output above")
    print("=" * 60)

if __name__ == "__main__":
    test()
