import sys
import os

# Add the parent directory to sys.path to allow imports from 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import SessionLocal, engine
from app.db.models import Base, User

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if test user exists
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        print("Creating test user...")
        user = User(
            username="testuser", 
            email="test@example.com",
            gender="Nam",
            age=20,
            height=172,
            weight=60
        )
        db.add(user)
        db.commit()
        print(f"Created user with ID: {user.id}")
    else:
        print(f"User testuser already exists with ID: {user.id}")
        
    db.close()

if __name__ == "__main__":
    init_db()
