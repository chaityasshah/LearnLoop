from pydantic import BaseModel, Field
from typing import Optional
import uuid
from .enums import Format, Difficulty

class LearningProfileBase(BaseModel):
    preferred_format: Format = Format.Visual
    typical_successful_minutes: int = Field(ge=1)
    current_difficulty: Difficulty = Difficulty.Intermediate
    available_minutes: int = Field(ge=0)
    long_activity_abandoned: bool = False

class LearningProfileUpdate(BaseModel):
    preferred_format: Optional[Format] = None
    typical_successful_minutes: Optional[int] = Field(None, ge=1)
    current_difficulty: Optional[Difficulty] = None
    available_minutes: Optional[int] = Field(None, ge=0)
    long_activity_abandoned: Optional[bool] = None

class LearningProfileResponse(LearningProfileBase):
    id: uuid.UUID
    student_id: uuid.UUID
    name: Optional[str] = None  # Student name, joined from student record

    model_config = {"from_attributes": True}
