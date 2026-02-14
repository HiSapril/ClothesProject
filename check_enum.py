from app.db.database import engine
from sqlalchemy import text

def check_enum():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT n.nspname as schema, t.typname as type, e.enumlabel as value FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'clothingtypeenum'"))
        rows = res.fetchall()
        print("Enum Values in DB:")
        for row in rows:
            print(f" - {row.value}")

if __name__ == "__main__":
    check_enum()
