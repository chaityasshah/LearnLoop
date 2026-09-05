from pydantic import BaseModel
from typing import Optional
import uuid
from .enums import ActivityKind, Difficulty, Format

class ActivityResponse(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    title: str
    kind: ActivityKind
    difficulty: Difficulty
    format: Format
    duration: int
    
    model_config = {"from_attributes": True}
