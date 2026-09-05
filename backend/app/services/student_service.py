from sqlalchemy.orm import Session
from app.models.student import Student, LearningProfile
from app.schemas.student import StudentCreate
from app.schemas.profile import LearningProfileBase, LearningProfileUpdate

def get_student(db: Session, student_id: str):
    return db.query(Student).filter(Student.id == student_id).first()

def create_student(db: Session, student: StudentCreate):
    db_student = Student(name=student.name, email=student.email)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    # Auto-create default learning profile
    db_profile = LearningProfile(
        student_id=db_student.id,
        preferred_format="Text",
        typical_successful_minutes=15,
        current_difficulty="Easy",
        available_minutes=30
    )
    db.add(db_profile)
    db.commit()
    
    return db_student

def get_profile(db: Session, student_id: str):
    return db.query(LearningProfile).filter(LearningProfile.student_id == student_id).first()

def create_profile(db: Session, student_id: str, profile: LearningProfileBase):
    db_profile = LearningProfile(
        student_id=student_id,
        preferred_format=profile.preferred_format.value,
        typical_successful_minutes=profile.typical_successful_minutes,
        current_difficulty=profile.current_difficulty.value,
        available_minutes=profile.available_minutes,
        long_activity_abandoned=profile.long_activity_abandoned
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_profile(db: Session, student_id: str, profile_update: LearningProfileUpdate):
    db_profile = get_profile(db, student_id)
    if not db_profile:
        return None
    
    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(value, "value"): # handle enums
            setattr(db_profile, key, value.value)
        else:
            setattr(db_profile, key, value)
            
    db.commit()
    db.refresh(db_profile)
    return db_profile
