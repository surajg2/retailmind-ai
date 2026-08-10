from fastapi import status
from backend.app.models.models import User

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"

def test_user_registration_and_password_hashing(client, db):
    test_email = "testowner@example.com"
    test_password = "SecurePassword123!"
    
    # Cleanup if exists
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()

    payload = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test Owner",
        "business_name": "Kirana Express",
        "business_type": "Kirana"
    }

    # 1. Register User
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    user_data = response.json()
    assert user_data["email"] == test_email
    assert user_data["full_name"] == "Test Owner"
    assert user_data["business"]["name"] == "Kirana Express"

    # 2. Verify Password Hashing in Database
    db_user = db.query(User).filter(User.email == test_email).first()
    assert db_user is not None
    assert db_user.hashed_password != test_password
    assert db_user.hashed_password.startswith("$2") # bcrypt hash prefix

def test_login_and_jwt_generation(client):
    test_email = "testowner@example.com"
    test_password = "SecurePassword123!"

    payload = {
        "email": test_email,
        "password": test_password
    }

    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert len(token_data["access_token"]) > 20

def test_protected_auth_me_endpoint(client):
    test_email = "testowner@example.com"
    test_password = "SecurePassword123!"

    # 1. Unauthenticated Request -> Reject 401
    unauth_resp = client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Authenticated Request with JWT -> Return User Profile
    login_resp = client.post("/api/v1/auth/login", json={"email": test_email, "password": test_password})
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == status.HTTP_200_OK
    user_info = me_resp.json()
    assert user_info["email"] == test_email
    assert user_info["business"]["name"] == "Kirana Express"
