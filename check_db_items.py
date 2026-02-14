from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import ClothingItem, User
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

users = db.query(User).all()
print(f"Total Users: {len(users)}")
for u in users:
    items = db.query(ClothingItem).filter(ClothingItem.user_id == u.id).all()
    print(f"User {u.id} ({u.username}): {len(items)} items")
    for i in items:
        print(f"  - Item {i.id}: Type={i.type}, Category={i.category_label}, Occasion={i.occasion}")

db.close()
