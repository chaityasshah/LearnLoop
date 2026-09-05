import pytest
from datetime import datetime, timedelta
import uuid

from app.models.event import LearningEvent, StateSnapshot
from scripts.export_training_data import extract_features
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_ml_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def create_synthetic_fixture():
    # Synthetic Fixture explicitly labeled for testing ML extraction without touching real DB
    db = TestingSessionLocal()
    db.query(LearningEvent).delete()
    db.commit()
    
    student_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    
    # Event 1: Completed, 2 hours ago
    e1 = LearningEvent(
        student_id=student_id,
        activity_id=activity_id,
        topic="Math",
        recommended_duration=10,
        actual_duration=10,
        difficulty="Easy",
        format="Visual",
        outcome="completed",
        feeling="easy",
        timestamp=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(e1)
    
    # Event 2: Struggled, 1 hour ago
    e2 = LearningEvent(
        student_id=student_id,
        activity_id=activity_id,
        topic="Math",
        recommended_duration=15,
        actual_duration=5,
        difficulty="Intermediate",
        format="Visual",
        outcome="partial",
        feeling="difficult",
        timestamp=datetime.utcnow() - timedelta(hours=1)
    )
    db.add(e2)
    
    db.commit()
    events = db.query(LearningEvent).all()
    db.close()
    return events

def test_feature_extraction():
    events = create_synthetic_fixture()
    dataset = extract_features(events)
    
    assert len(dataset) == 2
    
    # Check Row 1
    row1 = dataset[0]
    assert row1["target_completed"] == 1 # Completed
    assert row1["recent_completion_rate"] == 0.8 # Default/fallback since no prior history
    assert row1["consecutive_struggles"] == 0
    
    # Check Row 2 (Must not leak future data)
    row2 = dataset[1]
    assert row2["target_completed"] == 0 # Partial
    assert row2["recent_completion_rate"] == 1.0 # Knows about event 1 being completed
    assert row2["consecutive_struggles"] == 0 # Event 1 was completed
    assert row2["recent_struggle_count"] == 0 # Knows about event 1 only
    
    # Ensure no leakage (e.g., row 1 shouldn't know about event 2's struggle)
    assert row1["recent_struggle_count"] == 0

def test_no_future_data_leakage():
    events = create_synthetic_fixture()
    dataset = extract_features(events)
    # The first event happened before the second event.
    # The first event's extracted features should NOT contain any information about the second event.
    row1 = dataset[0]
    assert row1["recent_completion_rate"] == 0.8 # Base fallback, no events prior

def test_target_generation():
    events = create_synthetic_fixture()
    dataset = extract_features(events)
    assert dataset[0]["target_completed"] == 1
    assert dataset[1]["target_completed"] == 0

def test_synthetic_fixture_separation():
    # Verify that the TestingSessionLocal is entirely empty of real events
    db = TestingSessionLocal()
    assert db.query(LearningEvent).count() == 2 # Only the two we inserted in this module
    db.close()
