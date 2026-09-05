import os

base_dir = "backend"

files = {
    "requirements.txt": """fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic
pydantic-settings
pytest
httpx
python-dotenv
""",
    ".env.example": """DATABASE_URL=postgresql://postgres:password@localhost:5432/learnloop
""",
    "docker-compose.yml": """version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: learnloop
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""",
    "README.md": """# LearnLoop Backend

This is the FastAPI backend for the LearnLoop adaptive study system.

## Setup Instructions

1. **Create Python Environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Copy `.env.example` to `.env` and configure your database URL.
   ```bash
   cp .env.example .env
   ```

4. **Start PostgreSQL**:
   Use Docker Compose to start a local Postgres instance.
   ```bash
   docker-compose up -d
   ```

5. **Run FastAPI Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Run Tests**:
   ```bash
   pytest
   ```
""",
    "app/__init__.py": "",
    "app/main.py": """from fastapi import FastAPI
from app.api import students, activities, interactions
from app.db.session import engine
from app.models.base import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LearnLoop API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(students.router, prefix="/students", tags=["students"])
app.include_router(activities.router, prefix="/activities", tags=["activities"])
app.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
""",
    "app/api/__init__.py": "",
    "app/api/students.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_students():
    return {"message": "Placeholder for students"}
""",
    "app/api/activities.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_activities():
    return {"message": "Placeholder for activities"}
""",
    "app/api/interactions.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_interactions():
    return {"message": "Placeholder for interactions"}
""",
    "app/db/__init__.py": "",
    "app/db/session.py": """import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/learnloop")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
    "app/models/__init__.py": """from .base import Base
from .student import Student, LearningProfile
from .activity import Topic, Activity
from .event import LearningEvent, HelpRequest, StateSnapshot
""",
    "app/models/base.py": """from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
""",
    "app/models/student.py": """from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
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
""",
    "app/models/activity.py": """from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    parent_subject = Column(String)

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"))
    title = Column(String, nullable=False)
    kind = Column(String)
    difficulty = Column(String)
    format = Column(String)
    duration = Column(Integer)
    
    topic = relationship("Topic")
""",
    "app/models/event.py": """from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base

class LearningEvent(Base):
    __tablename__ = "learning_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
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
    consecutive_struggles = Column(Integer, default=0)
    consecutive_successes = Column(Integer, default=0)
    needs_revision = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
""",
    "app/schemas/__init__.py": "",
    "app/schemas/student.py": """from pydantic import BaseModel
import uuid
from datetime import datetime

class StudentBase(BaseModel):
    name: str
    email: str

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
""",
    "app/services/__init__.py": "",
    "tests/__init__.py": "",
    "tests/test_health.py": """from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
""",
    "tests/test_db.py": """import os
from app.db.session import DATABASE_URL, engine

def test_database_url_configured():
    assert DATABASE_URL is not None
    assert "postgresql://" in DATABASE_URL

def test_engine_creation():
    assert engine is not None
""",
    "tests/test_imports.py": """def test_models_importable():
    try:
        from app.models import Student, LearningProfile, Topic, Activity, LearningEvent, HelpRequest, StateSnapshot
    except ImportError as e:
        assert False, f"Models failed to import: {e}"

def test_schemas_importable():
    try:
        from app.schemas.student import StudentBase
    except ImportError as e:
        assert False, f"Schemas failed to import: {e}"
"""
}

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print(f"Successfully generated {len(files)} files in backend directory.")
