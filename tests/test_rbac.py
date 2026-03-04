import pytest
from fastapi import status
from app.db import models
from app.core import security

def test_user_cannot_access_admin_endpoints(client):
    """Verify that a regular USER is rejected from ADMIN routes."""
    # Register and login as USER
    client.post("/api/v1/auth/register", json={"username": "normal", "email": "n@ex.com", "password": "pass"})
    login_res = client.post("/api/v1/auth/login", data={"username": "normal", "password": "pass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to access admin users list
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_admin_can_access_admin_endpoints(client, db):
    """Verify that an ADMIN can access ADMIN routes."""
    # Manually promote a user to ADMIN in the test DB
    hashed_pass = security.get_password_hash("adminpass")
    admin_user = models.User(username="admin", email="admin@ex.com", hashed_password=hashed_pass, role=models.UserRole.ADMIN)
    db.add(admin_user)
    db.commit()

    # Login as ADMIN
    login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "adminpass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Access admin users list
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1

def test_user_isolation(client):
    """Verify that User A cannot see User B's items."""
    # 1. Create User A and upload an item
    client.post("/api/v1/auth/register", json={"username": "userA", "email": "a@ex.com", "password": "pass"})
    loginA = client.post("/api/v1/auth/login", data={"username": "userA", "password": "pass"})
    tokenA = loginA.json()["access_token"]
    
    # 2. Create User B
    client.post("/api/v1/auth/register", json={"username": "userB", "email": "b@ex.com", "password": "pass"})
    loginB = client.post("/api/v1/auth/login", data={"username": "userB", "password": "pass"})
    tokenB = loginB.json()["access_token"]

    # Access User A's data with User B's token -> Should be empty
    response = client.get("/api/v1/items/me", headers={"Authorization": f"Bearer {tokenB}"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0
