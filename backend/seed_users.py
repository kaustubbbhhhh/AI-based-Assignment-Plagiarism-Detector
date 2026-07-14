import requests

API_URL = "http://127.0.0.1:8000/api/auth/register"

users = [
    {
        "name": "Alice Student", "email": "student@demo.edu", "password": "pass123",
        "role": "student", "phone": "9876543210", "enrollment_no": "0901IT241001",
        "father_phone": "9876500001", "mother_phone": "9876500002",
        "section": "IT-4I1", "branch": "IT", "session": "2024-2028"
    },
    {
        "name": "Bob Teacher", "email": "teacher@demo.edu", "password": "pass123",
        "role": "teacher", "phone": "9876543211", "teacher_id": "FAC-2024-01",
        "branch": "IT", "section": "IT-4I1",
        "subjects_sections": [
            {"subject": "Database Management Systems", "section": "IT-4I1"},
            {"subject": "Programming in Java", "section": "IT-4I2"}
        ]
    },
    {
        "name": "Charlie HOD", "email": "hod@demo.edu", "password": "pass123",
        "role": "hod", "phone": "9876543212", "hod_id": "HOD-IT-01",
        "department": "IT", "branch": "IT"
    }
]

for user in users:
    try:
        res = requests.post(API_URL, json=user)
        print(f"[{res.status_code}] Seeding {user['email']}: {res.json().get('name', res.json())}")
    except Exception as e:
        print(f"Failed to seed {user['email']}: {e}")
