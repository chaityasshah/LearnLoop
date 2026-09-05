from sqlalchemy.orm import Session
from app.models.event import LearningEvent, HelpRequest
from app.schemas.event import HelpRequestCreate

def get_history(db: Session, student_id: str):
    return db.query(LearningEvent).filter(LearningEvent.student_id == student_id).order_by(LearningEvent.timestamp.desc()).all()

def create_help_request(db: Session, student_id: str, request: HelpRequestCreate):
    db_help = HelpRequest(
        student_id=student_id,
        context=request.context
    )
    db.add(db_help)
    db.commit()
    db.refresh(db_help)
    return db_help
