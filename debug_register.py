import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.db.database import SessionLocal
from app.db import models
from app.schemas import schemas
from app.core.auth import get_password_hash

def test_register():
    print("Starting registration diagnosis...")
    db = SessionLocal()
    try:
        username = "diag_user_3"
        email = "diag3@test.com"
        password = "password123"
        
        print(f"Checking if user {username} exists...")
        user = db.query(models.User).filter(
            (models.User.username == username) | (models.User.email == email)
        ).first()
        if user:
            print("User already exists, deleting for test...")
            db.delete(user)
            db.commit()

        print("Creating User object...")
        db_user = models.User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password)
        )
        print("Adding to DB...")
        db.add(db_user)
        print("Committing...")
        db.commit()
        print("Refreshing...")
        db.refresh(db_user)
        print("SUCCESS: User created successfully.")
    except Exception as e:
        print("FAILURE: Error occurred during registration:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_register()
