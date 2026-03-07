import sys
import traceback
from app.db.database import SessionLocal
from app.api.auth import register_user
from app.schemas.schemas import UserCreate
db = SessionLocal()
try:
    user_in = UserCreate(username='traceuser5', email='traceuser5@example.com', password='123')
    res = register_user(user_in=user_in, db=db)
    print('SUCCESS', res)
except Exception as e:
    traceback.print_exc()
