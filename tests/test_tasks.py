import pytest
from app.services.tasks import process_clothing_ai
from app.db import models
from app.domain.fashion_taxonomy import FashionCategory

def test_celery_task_mock_execution(mocker, db):
    user = models.User(username="taskuser", email="task@test.com")
    db.add(user)
    db.commit()
    
    item = models.ClothingItem(user_id=user.id, original_image_path="test.jpg", status="pending")
    db.add(item)
    db.commit()
    item_id = item.id
    
    mocker.patch("app.services.tasks.analyze_image", return_value={
        "processed_image_path": "proc.png",
        "color_hex": "#123456",
        "category_raw": "T-shirt",
        "confidence": 0.95,
        "raw_output": {}
    })
    mocker.patch("app.services.tasks.map_imagenet_label", return_value=FashionCategory.TOP)
    
    # First arg 'self' is None
    process_clothing_ai(None, item_id, "fake_hex")
    
    db.refresh(item)
    assert item.status == "COMPLETED"
    assert item.category == FashionCategory.TOP

def test_ai_task_idempotency(mocker, db):
    """Verify that redundant AI processing is skipped if item already completed."""
    user = models.User(username="idemp_user", email="id@test.com")
    db.add(user)
    db.commit()
    
    # Pre-existing completed item
    item = models.ClothingItem(
        user_id=user.id, 
        image_hash="same_hash", 
        status="COMPLETED", 
        category=FashionCategory.TOP
    )
    db.add(item)
    
    # New item with same hash
    new_item = models.ClothingItem(user_id=user.id, image_hash="same_hash", status="QUEUED")
    db.add(new_item)
    db.commit()
    
    # Mock analyze_image - should NOT be called
    mock_ai = mocker.patch("app.services.tasks.analyze_image")
    
    process_clothing_ai(None, new_item.id, "fake_hex")
    
    db.refresh(new_item)
    assert new_item.status == "COMPLETED"
    assert new_item.category == FashionCategory.TOP
    assert mock_ai.call_count == 0

def test_task_failure_propagation(mocker, db):
    """Verify that AI failures persist a reason to the DB."""
    user = models.User(username="fail_user", email="f@test.com")
    db.add(user)
    db.commit()
    
    item = models.ClothingItem(user_id=user.id, status="QUEUED")
    db.add(item)
    db.commit()
    
    # Mock AI to raise exception
    mocker.patch("app.services.tasks.analyze_image", side_effect=ValueError("Test AI Error"))
    
    from app.services.tasks import process_clothing_ai
    process_clothing_ai(None, item.id, "fake_hex")
    
    db.refresh(item)
    assert item.status == "FAILED"
    assert "Test AI Error" in item.failure_reason

def test_task_api_retryable_logic(client, db, mocker):
    """Verify API exposes retryable flag correctly."""
    user = models.User(username="retry_user", email="r@test.com")
    db.add(user)
    db.commit()
    
    # 1. System Error (Retryable)
    item_sys = models.ClothingItem(user_id=user.id, task_id="sys-task-1", status="FAILED", failure_reason="Timeout")
    db.add(item_sys)
    
    # 2. Logic Error (Not Retryable)
    item_logic = models.ClothingItem(user_id=user.id, task_id="logic-task-1", status="FAILED", failure_reason="No clothing found in image")
    db.add(item_logic)
    db.commit()
    
    # Mock Token for auth
    from app.core import security
    token = security.create_access_token({"sub": "retry_user"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Case 1
    res1 = client.get("/api/v1/items/task/sys-task-1", headers=headers)
    assert res1.json()["retryable"] is True
    
    # Case 2
    res2 = client.get("/api/v1/items/task/logic-task-1", headers=headers)
    assert res2.json()["retryable"] is False
