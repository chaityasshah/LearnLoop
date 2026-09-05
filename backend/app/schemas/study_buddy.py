from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    activity_id: str
    topic: str
    question: str
    current_difficulty: str
    history: List[dict] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
