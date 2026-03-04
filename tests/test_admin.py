import pytest
from fastapi import status
from app.db import models
from app.core import security

def test_admin_health_endpoint(client, db):
    # Setup Admin
    hashed_pass = security.get_password_hash("adminpass")
    admin_user = models.User(username="admin_health", email="ah@ex.com", hashed_password=hashed_pass, role=models.UserRole.ADMIN)
    db.add(admin_user)
    db.commit()

    login_res = client.post("/api/v1/auth/login", data={"username": "admin_health", "password": "adminpass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/admin/health", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"
    assert "database" in response.json()

def test_admin_metrics_endpoint(client, db):
    # Setup Admin
    hashed_pass = security.get_password_hash("adminpass")
    admin_user = models.User(username="admin_metrics", email="am@ex.com", hashed_password=hashed_pass, role=models.UserRole.ADMIN)
    db.add(admin_user)
    db.commit()

    login_res = client.post("/api/v1/auth/login", data={"username": "admin_metrics", "password": "adminpass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add some data
    db_item = models.ClothingItem(user_id=admin_user.id, status="completed")
    db.add(db_item)
    db.commit()

    response = client.get("/api/v1/admin/metrics", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total_items"] >= 1
    assert "items_by_status" in response.json()

def test_admin_task_inspection(client, db, mocker):
    # Setup Admin
    hashed_pass = security.get_password_hash("adminpass")
    admin_user = models.User(username="admin_task", email="at@ex.com", hashed_password=hashed_pass, role=models.UserRole.ADMIN)
    db.add(admin_user)
    db.commit()

    login_res = client.post("/api/v1/auth/login", data={"username": "admin_task", "password": "adminpass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mock Celery AsyncResult
    mock_result = mocker.patch("app.api.admin_ops.AsyncResult")
    mock_result.return_value.status = "SUCCESS"
    mock_result.return_value.ready.return_value = True
    mock_result.return_value.failed.return_value = False

    response = client.get("/api/v1/admin/tasks/fake-uuid", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "SUCCESS"
