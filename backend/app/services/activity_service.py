from sqlalchemy.orm import Session
from app.models.activity import Activity

def get_activities(db: Session):
    return db.query(Activity).all()

def get_activity(db: Session, activity_id: str):
    return db.query(Activity).filter(Activity.id == activity_id).first()
