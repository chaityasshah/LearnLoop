from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base

class LearningEvent(Base):
    __tablename__ = "learning_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("state_snapshots.id"), nullable=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id"))
    topic = Column(String)
    recommended_duration = Column(Integer)
    actual_duration = Column(Integer)
    difficulty = Column(String)
    format = Column(String)
    outcome = Column(String)
    feeling = Column(String)
    response_time = Column(Integer)
    help_requested = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class HelpRequest(Base):
    __tablename__ = "help_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("learning_events.id"), nullable=True)
    context = Column(String)
    resolved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class StateSnapshot(Base):
    __tablename__ = "state_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    
    # State at recommendation time
    available_minutes = Column(Integer)
    current_difficulty = Column(String)
    typical_successful_minutes = Column(Integer)
    
    # Engine output
    recommendation_score = Column(Integer)
    
    # Optional historical aggregates if we want to cache them, but we can compute them.
    # We will just rely on timestamp to reconstruct history.
    
    timestamp = Column(DateTime, default=datetime.utcnow)
