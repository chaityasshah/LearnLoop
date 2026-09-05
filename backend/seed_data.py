import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.student import Student, LearningProfile
from app.models.activity import Topic, Activity
from app.models.event import LearningEvent
from app.db.session import DATABASE_URL
import uuid

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Could not connect to DB for seeding: {e}")
        return

    db = SessionLocal()
    
    # 1. Student Aarav
    if not db.query(Student).filter(Student.email == "aarav@learnloop.local").first():
        aarav = Student(name="Aarav", email="aarav@learnloop.local")
        db.add(aarav)
        db.commit()
        db.refresh(aarav)
        
        profile = LearningProfile(
            student_id=aarav.id,
            preferred_format="Visual",
            typical_successful_minutes=12,
            current_difficulty="Intermediate",
            available_minutes=20,
            long_activity_abandoned=True
        )
        db.add(profile)
        db.commit()
        
    # Topics
    topics_data = ["Fractions", "Multiplication", "Plant cells", "Photosynthesis", "Algorithms", "Sentences"]
    topic_map = {}
    for t in topics_data:
        topic = db.query(Topic).filter(Topic.name == t).first()
        if not topic:
            topic = Topic(name=t, parent_subject="Unknown")
            db.add(topic)
            db.commit()
            db.refresh(topic)
        topic_map[t] = topic.id
        
    # Activities (matching current mock library)
    activities_data = [
        {"title": "Equivalent Fractions with Pictures", "topic_name": "Fractions", "kind": "Practice", "difficulty": "Easy", "format": "Visual", "duration": 10},
        {"title": "Fractions with Guided Visual Support", "topic_name": "Fractions", "kind": "Revision", "difficulty": "Easy", "format": "Visual", "duration": 10},
        {"title": "Compare Equivalent Fractions", "topic_name": "Fractions", "kind": "Practice", "difficulty": "Intermediate", "format": "Visual", "duration": 15},
        {"title": "Add Fractions with Different Denominators", "topic_name": "Fractions", "kind": "Learn", "difficulty": "Challenging", "format": "Visual", "duration": 20},
        {"title": "Multiplication Patterns to 10", "topic_name": "Multiplication", "kind": "Revision", "difficulty": "Easy", "format": "Visual", "duration": 10},
        {"title": "Two-Digit Multiplication Strategy", "topic_name": "Multiplication", "kind": "Practice", "difficulty": "Intermediate", "format": "Text", "duration": 15},
        {"title": "Multi-Step Multiplication Problems", "topic_name": "Multiplication", "kind": "Practice", "difficulty": "Challenging", "format": "Text", "duration": 20},
        {"title": "How Plant Cells Work", "topic_name": "Plant cells", "kind": "Learn", "difficulty": "Intermediate", "format": "Visual", "duration": 15},
        {"title": "The Photosynthesis Equation", "topic_name": "Photosynthesis", "kind": "Learn", "difficulty": "Challenging", "format": "Visual", "duration": 20},
        {"title": "Step-by-Step Algorithms", "topic_name": "Algorithms", "kind": "Learn", "difficulty": "Intermediate", "format": "Text", "duration": 15},
        {"title": "Search Algorithms: Linear vs Binary", "topic_name": "Algorithms", "kind": "Learn", "difficulty": "Challenging", "format": "Text", "duration": 20},
        {"title": "Build Simple Sentences", "topic_name": "Sentences", "kind": "Practice", "difficulty": "Easy", "format": "Visual", "duration": 10}
    ]
    
    for a in activities_data:
        if not db.query(Activity).filter(Activity.title == a["title"]).first():
            act = Activity(
                topic_id=topic_map[a["topic_name"]],
                title=a["title"],
                kind=a["kind"],
                difficulty=a["difficulty"],
                format=a["format"],
                duration=a["duration"]
            )
            db.add(act)
    
    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
