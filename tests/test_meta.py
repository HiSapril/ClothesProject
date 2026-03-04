import pytest
from fastapi import status

def test_get_meta_enums(client):
    response = client.get("/api/v1/meta/enums")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "fashion_categories" in data
    assert "TOP" in data["fashion_categories"]
    assert "classification_statuses" in data
    assert "CONFIRMED" in data["classification_statuses"]
    assert "occasions" in data
    assert "casual" in data["occasions"]
    assert "user_roles" in data
    assert "admin" in data["user_roles"]
