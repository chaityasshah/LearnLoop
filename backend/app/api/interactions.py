from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.db.session import get_db
from app.schemas.event import LearningEventResponse, HelpRequestCreate, HelpRequestResponse
from app.services import interaction_service
from app.services.engine_adapter import get_recommendation_for_student
from app.models.activity import Activity
from app.models.student import LearningProfile
from app.models.event import LearningEvent, StateSnapshot
from pydantic import BaseModel
from app.schemas.enums import Outcome, Feeling
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class SessionOutcomeRequest(BaseModel):
    actual_duration: int
    outcome: Outcome
    feeling: Feeling
    snapshot_id: str = None
    response_time: Optional[int] = 0

@router.get("/{student_id}/history", response_model=List[LearningEventResponse])
def get_history(student_id: uuid.UUID, db: Session = Depends(get_db)):
    return interaction_service.get_history(db, student_id)

@router.post("/{student_id}/activities/{activity_id}/outcome")
def process_session_outcome(student_id: uuid.UUID, activity_id: uuid.UUID, event: SessionOutcomeRequest, db: Session = Depends(get_db)):
    try:
        # Check idempotency first: has this snapshot already been completed?
        if event.snapshot_id:
            try:
                snapshot_uuid = uuid.UUID(event.snapshot_id)
                existing_event = db.query(LearningEvent).filter(LearningEvent.snapshot_id == snapshot_uuid).first()
                if existing_event:
                    # Already processed. Return existing data and fetch a recommendation 
                    # without modifying the profile twice.
                    logger.info(f"Idempotency hit: Outcome for snapshot {snapshot_uuid} already processed for student {student_id}")
                    return {
                        "event": {
                            "id": str(existing_event.id),
                            "student_id": str(existing_event.student_id),
                            "activity_id": str(existing_event.activity_id),
                            "outcome": existing_event.outcome,
                            "feeling": existing_event.feeling
                        },
                        "recommendation": get_recommendation(student_id, db)
                    }
            except ValueError:
                pass # Invalid UUID format, proceed to standard validation
                
        # Fetch topic from activity
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        snapshot_uuid = uuid.UUID(event.snapshot_id) if event.snapshot_id else None
        
        # Verify the snapshot belongs to the student if it exists
        if snapshot_uuid:
            snapshot = db.query(StateSnapshot).filter(StateSnapshot.id == snapshot_uuid).first()
            if snapshot and snapshot.student_id != student_id:
                raise HTTPException(status_code=400, detail="Snapshot does not belong to this student")

        db_event = LearningEvent(
            student_id=student_id,
            snapshot_id=snapshot_uuid,
            activity_id=activity_id,
            topic=activity.topic.name if hasattr(activity.topic, "name") else str(activity.topic),
            recommended_duration=activity.duration,
            actual_duration=event.actual_duration,
            difficulty=activity.difficulty,
            format=activity.format,
            outcome=event.outcome.value,
            feeling=event.feeling.value,
            response_time=event.response_time
        )
        db.add(db_event)
        
        # Update profile based on outcome
        profile = db.query(LearningProfile).filter(LearningProfile.student_id == student_id).first()
        if profile:
            from app.services.engine_adapter import DomainProfile, DomainActivity
            from app.services.adaptive_engine import update_learning_profile
            
            # Get full history for the topic
            history = db.query(LearningEvent).filter(LearningEvent.student_id == student_id).all()
            
            domain_profile = DomainProfile(profile)
            domain_activity = DomainActivity(activity)
            
            # We need mock history objects for the engine
            class MockEvent:
                pass
            
            history_mocks = []
            for h in history:
                m = MockEvent()
                m.topic = h.topic
                m.outcome = Outcome(h.outcome)
                m.feeling = Feeling(h.feeling)
                m.actual_duration = h.actual_duration or 0
                history_mocks.append(m)
                
            m_curr = MockEvent()
            m_curr.topic = domain_activity.topic
            m_curr.outcome = event.outcome
            m_curr.feeling = event.feeling
            m_curr.actual_duration = event.actual_duration
            history_mocks.append(m_curr)
                
            updated = update_learning_profile(domain_profile, domain_activity, event.outcome, event.feeling, history_mocks)
            
            profile.recent_completion_rate = updated.recent_completion_rate
            profile.completed_today = updated.completed_today
            profile.repeated_mistakes = updated.repeated_mistakes
            profile.revision_topics = updated.revision_topics
            profile.typical_successful_minutes = updated.typical_successful_minutes
            profile.current_difficulty = updated.current_difficulty.value if hasattr(updated.current_difficulty, "value") else updated.current_difficulty
            profile.long_activity_abandoned = updated.long_activity_abandoned
            
            # Data Integrity: Prevent negative available_minutes
            profile.available_minutes = max(0, updated.available_minutes)
            
            logger.info(f"Profile updated for student {student_id}: completion_rate={profile.recent_completion_rate}, diff={profile.current_difficulty}")
            
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Outcome recorded: student={student_id}, activity={activity_id}, outcome={db_event.outcome}")
        
        return {
            "event": {
                "id": str(db_event.id),
                "student_id": str(db_event.student_id),
                "activity_id": str(db_event.activity_id),
                "outcome": db_event.outcome,
                "feeling": db_event.feeling
            },
            "recommendation": get_recommendation(student_id, db)
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error processing outcome: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process session outcome safely")

@router.post("/{student_id}/help-request", response_model=HelpRequestResponse)
def create_help_request(student_id: uuid.UUID, request: HelpRequestCreate, db: Session = Depends(get_db)):
    logger.info(f"Help request created for student {student_id}")
    # Add to explanation_requests in profile if column exists
    profile = db.query(LearningProfile).filter(LearningProfile.student_id == student_id).first()
    if profile and hasattr(profile.__class__, "explanation_requests"):
        profile.explanation_requests = (getattr(profile, "explanation_requests") or 0) + 1
        db.commit()
    return interaction_service.create_help_request(db, student_id, request)

@router.get("/{student_id}/recommendation")
def get_recommendation(student_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = db.query(LearningProfile).filter(LearningProfile.student_id == student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    history = db.query(LearningEvent).filter(LearningEvent.student_id == student_id).order_by(LearningEvent.timestamp.asc()).all()
    activities = db.query(Activity).all()
    
    rec = get_recommendation_for_student(activities, profile, history)
    
    from app.models.event import StateSnapshot
    snapshot = StateSnapshot(
        student_id=student_id,
        available_minutes=profile.available_minutes,
        current_difficulty=profile.current_difficulty,
        typical_successful_minutes=profile.typical_successful_minutes,
        recommendation_score=rec["score"]
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    logger.info(f"Recommendation generated for student {student_id}: activity={rec['activity'].id}, snapshot={snapshot.id}")
    
    # Needs to match frontend Recommendation shape exactly
    # Activity objects in rec contain Enums which may not serialize directly if passed as is
    
    # Map to frontend shape
    return {
        "snapshot_id": str(snapshot.id),
        "activity": {
            "id": rec["activity"].id,
            "topic": rec["activity"].topic,
            "title": rec["activity"].title,
            "duration": rec["activity"].duration,
            "difficulty": rec["activity"].difficulty.value,
            "format": rec["activity"].format.value,
            "kind": rec["activity"].kind.value,
        },
        "duration": rec["duration"],
        "difficulty": rec["difficulty"].value,
        "format": rec["format"].value,
        "kind": rec["kind"].value,
        "breakMinutes": rec["breakMinutes"],
        "supportNeeded": rec["supportNeeded"],
        "score": rec["score"],
        "reasons": rec["reasons"],
        "bullets": rec["bullets"],
        "flags": rec["flags"]
    }

from app.schemas.study_buddy import ChatRequest, ChatResponse
from app.services.study_buddy_service import study_buddy_service

@router.post("/{student_id}/chat", response_model=ChatResponse)
def get_chat_response(student_id: uuid.UUID, request: ChatRequest):
    logger.info(f"Study Buddy chat requested for student {student_id}, topic: {request.topic}")
    try:
        response = study_buddy_service.generate_response(
            question=request.question,
            topic=request.topic,
            difficulty=request.current_difficulty,
            history=request.history
        )
        return ChatResponse(
            answer=response["answer"],
            sources=response["sources"]
        )
    except Exception as e:
        logger.error(f"Study Buddy failed for {student_id}: {e}")
        raise HTTPException(status_code=503, detail="Study Buddy is currently offline. Please try again later.")
