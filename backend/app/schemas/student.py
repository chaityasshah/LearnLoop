from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class StudentBase(BaseModel):
    name: str
    email: str

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: uuid.UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}
