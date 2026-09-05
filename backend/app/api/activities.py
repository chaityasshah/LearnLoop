from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.db.session import get_db
from app.schemas.activity import ActivityResponse
from app.services import activity_service

router = APIRouter()

@router.get("/", response_model=List[ActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    return activity_service.get_activities(db)

@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(activity_id: uuid.UUID, db: Session = Depends(get_db)):
    activity = activity_service.get_activity(db, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity
