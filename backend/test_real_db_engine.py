import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from app.db.session import DATABASE_URL
from app.models.student import Student, LearningProfile
from app.models.activity import Activity
from app.models.event import LearningEvent
from app.services.engine_adapter import get_recommendation_for_student

def run_real_db_test():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # 1. Get Aarav
    student = db.query(Student).filter(Student.email == "aarav@learnloop.local").first()
    if not student:
        print("Student not found. Did you run the seed script?")
        return
        
    print(f"Testing engine for student: {student.name}")
    
    # 2. Get Profile
    profile = db.query(LearningProfile).filter(LearningProfile.student_id == student.id).first()
    
    # 3. Get History
    history = db.query(LearningEvent).filter(LearningEvent.student_id == student.id).order_by(LearningEvent.timestamp.asc()).all()
    
    # 4. Get Activities
    activities = db.query(Activity).all()
    
    print(f"Found {len(history)} history events, {len(activities)} activities.")
    
    # 5. Run Engine
    rec = get_recommendation_for_student(activities, profile, history)
    
    print("\n================ RECOMMENDATION ================")
    print(f"Activity: {rec['activity'].title} ({rec['activity'].topic})")
    print(f"Duration: {rec['duration']} mins")
    print(f"Difficulty: {rec['difficulty'].value}")
    print(f"Format: {rec['format'].value}")
    print(f"Kind: {rec['kind'].value}")
    print(f"Break: {rec['breakMinutes']} mins")
    print(f"Support Needed: {rec['supportNeeded']}")
    print("Reasons:", rec['reasons'][0])
    print("Bullets:", rec['bullets'])
    print("Flags:", rec['flags'])
    
    db.close()

if __name__ == "__main__":
    run_real_db_test()
