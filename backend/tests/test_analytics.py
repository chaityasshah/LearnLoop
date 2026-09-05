import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
from datetime import datetime

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models.student import LearningProfile
from app.models.event import LearningEvent, StateSnapshot

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Insert some mock data for analytics
    student_id = uuid.uuid4()
    profile = LearningProfile(
        student_id=student_id,
        preferred_format="Visual",
        typical_successful_minutes=20,
        current_difficulty="Intermediate",
        available_minutes=60
    )
    db.add(profile)
    
    # A valid snapshot
    snapshot_id = uuid.uuid4()
    snapshot = StateSnapshot(
        id=snapshot_id,
        student_id=student_id,
        available_minutes=60,
        current_difficulty="Intermediate",
        typical_successful_minutes=20,
        recommendation_score=90.0,
        timestamp=datetime.utcnow()
    )
    db.add(snapshot)
    
    # An event with the snapshot
    event = LearningEvent(
        id=uuid.uuid4(),
        student_id=student_id,
        snapshot_id=snapshot_id,
        activity_id=uuid.uuid4(),
        topic="Math",
        recommended_duration=10,
        actual_duration=10,
        difficulty="Intermediate",
        format="Visual",
        outcome="completed",
        feeling="easy",
        timestamp=datetime.utcnow()
    )
    db.add(event)
    
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)

def test_get_analytics():
    response = client.get("/api/analytics/")
    assert response.status_code == 200
    data = response.json()
    
    metrics = data["metrics"]
    assert metrics["total_sessions"] == 1
    assert metrics["completed_sessions"] == 1
    assert metrics["completion_rate"] == 1.0
    assert metrics["avg_recommended_duration"] == 10.0
    assert metrics["events_with_valid_snapshot"] == 1
    
    integrity = data["integrity_checks"]
    assert integrity["events_without_snapshot"] == 0
    assert integrity["duplicate_outcome_submissions"] == 0
    assert integrity["future_data_leakage_detected"] is False
