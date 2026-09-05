from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base

class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profile = relationship("LearningProfile", back_populates="student", uselist=False)

class LearningProfile(Base):
    __tablename__ = "learning_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    preferred_format = Column(String)
    typical_successful_minutes = Column(Integer)
    current_difficulty = Column(String)
    available_minutes = Column(Integer)
    long_activity_abandoned = Column(Boolean, default=False)
    
    student = relationship("Student", back_populates="profile")
