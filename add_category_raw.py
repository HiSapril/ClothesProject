from app.db.database import engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS category_raw VARCHAR"))
            conn.commit()
            print("Added category_raw column")
        except Exception as e:
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
