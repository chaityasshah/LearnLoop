import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from app.db.session import SessionLocal

def fix_aarav():
    db = SessionLocal()
    db.execute(text("UPDATE students SET is_demo = TRUE WHERE email = 'aarav@learnloop.local'"))
    db.commit()
    print("Fixed aarav is_demo")

if __name__ == "__main__":
    fix_aarav()
