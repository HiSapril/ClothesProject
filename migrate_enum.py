from app.db.database import engine
from sqlalchemy import text

def migrate():
    new_values = ['eyewear', 'bracelet', 'watch', 'necklace']
    with engine.connect() as conn:
        for val in new_values:
            try:
                # Use a separate transaction for each ALTER TYPE as they can't be in a block sometimes
                conn.execute(text(f"ALTER TYPE clothingtypeenum ADD VALUE IF NOT EXISTS '{val}'"))
                conn.commit()
                print(f"Added {val}")
            except Exception as e:
                print(f"Skipping {val} (exists or error): {e}")

if __name__ == "__main__":
    migrate()
