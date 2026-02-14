from app.db.database import engine
from sqlalchemy import text

def migrate():
    print("Starting migration...")
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_token TEXT"))
            conn.commit()
        print("Migration successful: added google_token column.")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("Column google_token already exists.")
        else:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
