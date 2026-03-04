import pytest
from fastapi import status

def test_register_and_login(client):
    """Test the full registration and login flow."""
    # 1. Register
    reg_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "testuser"

    # 2. Login
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_protected_endpoint_access(client):
    """Test access to protected endpoints with and without tokens."""
    # Register and login
    client.post("/api/v1/auth/register", json={"username": "user1", "email": "u1@ex.com", "password": "pass"})
    login_res = client.post("/api/v1/auth/login", data={"username": "user1", "password": "pass"})
    token = login_res.json()["access_token"]

    # 1. Access without token -> Fail
    response = client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Access with valid token -> Success
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "user1"

def test_token_refresh(client):
    """Test refreshing an access token using a refresh token."""
    client.post("/api/v1/auth/register", json={"username": "refuser", "email": "r@ex.com", "password": "pass"})
    login_res = client.post("/api/v1/auth/login", data={"username": "refuser", "password": "pass"})
    refresh_token = login_res.json()["refresh_token"]

    # Refresh
    response = client.post(f"/api/v1/auth/refresh?refresh_token={refresh_token}")
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

def test_logout_revocation(client):
    """Test that logging out revokes the refresh token."""
    client.post("/api/v1/auth/register", json={"username": "outuser", "email": "o@ex.com", "password": "pass"})
    login_res = client.post("/api/v1/auth/login", data={"username": "outuser", "password": "pass"})
    
    # Get user_id from /users/me
    token = login_res.json()["access_token"]
    me_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me_res.json()["id"]
    refresh_token = login_res.json()["refresh_token"]

    # Logout
    logout_res = client.post(f"/api/v1/auth/logout?user_id={user_id}")
    assert logout_res.status_code == status.HTTP_200_OK

    # Try to refresh -> Should fail
    refresh_res = client.post(f"/api/v1/auth/refresh?refresh_token={refresh_token}")
    assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED
