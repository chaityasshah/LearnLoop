import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import SessionLocal

def migrate():
    print("Starting DB migration for Provenance and Response Time...")
    db = SessionLocal()
    try:
        # Add is_demo to students
        try:
            db.execute(text("ALTER TABLE students ADD COLUMN is_demo BOOLEAN DEFAULT FALSE NOT NULL"))
            print("Added is_demo column to students.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("is_demo column already exists.")
            else:
                print(f"Error adding is_demo: {e}")
                db.rollback()

        # Update existing records to mark synthetic demo
        db.execute(text("UPDATE students SET is_demo = TRUE WHERE name LIKE '%SYNTHETIC DEMO%'"))
        
        # Add response_time to learning_events (It might already exist, but just in case)
        try:
            db.execute(text("ALTER TABLE learning_events ADD COLUMN response_time INTEGER"))
            print("Added response_time column to learning_events.")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("response_time column already exists.")
            else:
                print(f"Error adding response_time: {e}")
                db.rollback()

        db.commit()
        print("Migration complete.")
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
