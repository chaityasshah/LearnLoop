from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from .enums import Difficulty, Format, Outcome, Feeling

class LearningEventBase(BaseModel):
    activity_id: uuid.UUID
    topic: str
    recommended_duration: int
    actual_duration: int
    difficulty: Difficulty
    format: Format
    outcome: Outcome
    feeling: Feeling
    response_time: Optional[int] = 0
    help_requested: bool = False

class LearningEventCreate(LearningEventBase):
    pass

class LearningEventResponse(LearningEventBase):
    id: uuid.UUID
    student_id: uuid.UUID
    timestamp: datetime
    
    model_config = {"from_attributes": True}

class HelpRequestCreate(BaseModel):
    activity_id: uuid.UUID
    context: str

class HelpRequestResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    event_id: Optional[uuid.UUID] = None
    context: str
    resolved: bool
    timestamp: datetime

    model_config = {"from_attributes": True}
