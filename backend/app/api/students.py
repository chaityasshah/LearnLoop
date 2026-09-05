from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.db.session import get_db
from app.schemas.student import StudentCreate, StudentResponse
from app.schemas.profile import LearningProfileResponse, LearningProfileUpdate, LearningProfileBase
from app.services import student_service
from app.models.student import Student
from typing import Any

router = APIRouter()

@router.post("/", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    return student_service.create_student(db, student)

@router.get("/demo", response_model=StudentResponse)
def get_demo_student(db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == "aarav@learnloop.local").first()
    if not student:
        raise HTTPException(status_code=404, detail="Demo student not found")
    return student

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.get("/{student_id}/profile", response_model=LearningProfileResponse)
def get_profile(student_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = student_service.get_profile(db, student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Enrich response with student name from the related Student record
    student = db.query(Student).filter(Student.id == student_id).first()
    response = LearningProfileResponse.model_validate(profile)
    if student:
        response.name = student.name
    return response

@router.patch("/{student_id}/profile", response_model=LearningProfileResponse)
def update_profile(student_id: uuid.UUID, profile_update: LearningProfileUpdate, db: Session = Depends(get_db)):
    profile = student_service.update_profile(db, student_id, profile_update)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/{student_id}/reset")
def reset_student_data(student_id: uuid.UUID, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # PHASE 13I: Safety block - only allow resetting if is_demo is True
    if not student.is_demo:
        raise HTTPException(status_code=403, detail="Cannot reset non-demo student records.")
        
    from app.models.event import LearningEvent, StateSnapshot, HelpRequest
    
    # Delete dependent records
    db.query(HelpRequest).filter(HelpRequest.student_id == student_id).delete()
    db.query(LearningEvent).filter(LearningEvent.student_id == student_id).delete()
    db.query(StateSnapshot).filter(StateSnapshot.student_id == student_id).delete()
    
    db.commit()
    return {"status": "success", "message": "Demo student data reset"}
