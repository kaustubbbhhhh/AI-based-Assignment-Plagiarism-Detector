"""
Test suite for Forgot Password & Reset Password feature.
"""

import sys
import os

# Add backend directory to sys.path so we can import models, dependencies, etc.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_URL"] = "sqlite:///./plagiarism.db"


from fastapi.testclient import TestClient
from main import app
from core.database import Base, engine, SessionLocal
from models.user import User, UserRole
from core.security import hash_password, verify_password

client = TestClient(app)

def test_forgot_password_workflow():
    print("=" * 60)
    print(" Running Forgot Password & Reset Password Workflow Test")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    test_email = "testresetuser@example.com"
    old_password = "oldpassword123"
    new_password = "newpassword456"

    # Clean up test user if existing
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()

    # 1. Create a test user directly in DB
    user = User(
        name="Reset Test User",
        email=test_email,
        hashed_password=hash_password(old_password),
        role=UserRole.student,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[PASS] Created test user: {user.email} (ID: {user.id})")

    # 2. Test Login with old password
    login_resp = client.post("/api/auth/login", json={"email": test_email, "password": old_password})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.json()}"
    print("[PASS] Initial login with old password succeeded.")

    # 3. Test Forgot Password endpoint
    forgot_resp = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert forgot_resp.status_code == 200, f"Forgot password failed: {forgot_resp.json()}"
    data = forgot_resp.json()
    assert "message" in data
    assert data.get("reset_link") is not None
    reset_link = data["reset_link"]
    token = reset_link.split("token=")[1]
    print(f"[PASS] Forgot password returned reset token: {token[:20]}...")

    # 4. Test Reset Password endpoint with short password (should fail validation)
    bad_reset_resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": "12"})
    assert bad_reset_resp.status_code == 400
    print("[PASS] Short password rejected correctly (400).")

    # 5. Test Reset Password endpoint with valid token & new password
    reset_resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": new_password})
    assert reset_resp.status_code == 200, f"Reset password failed: {reset_resp.json()}"
    print("[PASS] Password reset succeeded.")

    # 6. Test Login with old password (should now fail)
    old_login_resp = client.post("/api/auth/login", json={"email": test_email, "password": old_password})
    assert old_login_resp.status_code == 401
    print("[PASS] Login with OLD password rejected (401).")

    # 7. Test Login with new password (should succeed)
    new_login_resp = client.post("/api/auth/login", json={"email": test_email, "password": new_password})
    assert new_login_resp.status_code == 200, f"New password login failed: {new_login_resp.json()}"
    print("[PASS] Login with NEW password succeeded.")

    # 8. Test re-using the same reset token (should fail because pwd_sig changed!)
    reused_reset_resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": "anotherpassword"})
    assert reused_reset_resp.status_code == 400
    print("[PASS] Single-use validation rejected re-used reset token (400).")

    # Cleanup
    db.delete(user)
    db.commit()
    db.close()
    print("\n[SUCCESS] ALL FORGOT PASSWORD TESTS PASSED!")

if __name__ == "__main__":
    test_forgot_password_workflow()
