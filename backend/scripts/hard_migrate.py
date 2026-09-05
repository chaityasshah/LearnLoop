import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from app.db.session import engine

def hard_migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN is_demo BOOLEAN DEFAULT FALSE NOT NULL"))
            conn.commit()
            print("Added is_demo")
        except Exception as e:
            print(f"Failed to add is_demo: {e}")
            conn.rollback()

        try:
            conn.execute(text("UPDATE students SET is_demo = TRUE WHERE email = 'aarav@learnloop.local' OR name LIKE '%SYNTHETIC DEMO%'"))
            conn.commit()
            print("Updated Aarav and Demo")
        except Exception as e:
            print(f"Failed to update: {e}")
            conn.rollback()

if __name__ == "__main__":
    hard_migrate()
