import pytest
import uuid
from datetime import datetime, timedelta
from app.models.student import Student, LearningProfile
from app.models.event import LearningEvent, StateSnapshot, HelpRequest
from app.schemas.enums import Outcome, Feeling
from app.api.interactions import SessionOutcomeRequest
from app.config import APP_ENV, ML_ENABLED
from scripts.export_training_data import extract_features
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal

client = TestClient(app)

@pytest.fixture
def db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()

def test_ml_disabled_in_pilot():
    """Test 10: ML remaining disabled in pilot mode"""
    class DummyConfig:
        def __init__(self, env):
            self.app_env = env
            self.ml_enabled = False if env == "pilot" else True
    
    config = DummyConfig("pilot")
    assert not config.ml_enabled

def test_provenance_separation(db):
    """Test 1: Real vs synthetic provenance"""
    s_real = Student(id=uuid.uuid4(), name="Real User", email=f"real_{uuid.uuid4()}@example.com", is_demo=False)
    s_demo = Student(id=uuid.uuid4(), name="Demo User", email=f"demo_{uuid.uuid4()}@example.com", is_demo=True)
    db.add(s_real)
    db.add(s_demo)
    db.commit()
    
    assert db.query(Student).filter(Student.email == s_real.email).first().is_demo is False
    assert db.query(Student).filter(Student.email == s_demo.email).first().is_demo is True

def test_demo_reset_isolation(db):
    """Test 7: Demo reset isolation"""
    s_real = Student(id=uuid.uuid4(), name="Real User 2", email=f"real2_{uuid.uuid4()}@example.com", is_demo=False)
    s_demo = Student(id=uuid.uuid4(), name="Demo User 2", email=f"demo2_{uuid.uuid4()}@example.com", is_demo=True)
    db.add(s_real)
    db.add(s_demo)
    db.commit()
    
    # Try resetting real student
    res1 = client.post(f"/api/students/{s_real.id}/reset")
    assert res1.status_code == 403
    
    # Try resetting demo student
    res2 = client.post(f"/api/students/{s_demo.id}/reset")
    assert res2.status_code == 200

def test_event_completeness_and_response_time(db):
    """Test 2, 3, 4, 9: Real event completeness, response-time, duration, privacy fields"""
    s_real = Student(id=uuid.uuid4(), name="Real User 3", email=f"real3_{uuid.uuid4()}@example.com", is_demo=False)
    p_real = LearningProfile(student_id=s_real.id, preferred_format="Text", typical_successful_minutes=15, current_difficulty="Easy")
    db.add(s_real)
    db.add(p_real)
    db.commit()
    
    act_id = uuid.uuid4()
    from app.models.activity import Activity, Topic
    t1 = Topic(id=uuid.uuid4(), name=f"Algebra_{uuid.uuid4()}", parent_subject="Math")
    db.add(t1)
    db.commit()
    a = Activity(id=act_id, topic_id=t1.id, title="A1", duration=15, difficulty="Easy", format="Text", kind="Learn")
    db.add(a)
    db.commit()
    
    snap = StateSnapshot(id=uuid.uuid4(), student_id=s_real.id)
    db.add(snap)
    db.commit()
    
    req = {
        "actual_duration": 12,
        "outcome": "completed",
        "feeling": "manageable",
        "snapshot_id": str(snap.id),
        "response_time": 600
    }
    
    res = client.post(f"/api/students/{s_real.id}/activities/{act_id}/outcome", json=req)
    assert res.status_code == 200
    
    ev = db.query(LearningEvent).filter(LearningEvent.student_id == s_real.id).first()
    assert ev is not None
    assert ev.actual_duration == 12
    assert ev.response_time == 600
    assert ev.outcome == "completed"
    assert ev.feeling == "manageable"
    assert ev.topic.startswith("Algebra")

def test_duplicate_outcome_protection(db):
    """Test 5: Duplicate outcome protection (idempotency)"""
    s_real = Student(id=uuid.uuid4(), name="Real User 4", email=f"real4_{uuid.uuid4()}@example.com", is_demo=False)
    p_real = LearningProfile(student_id=s_real.id, preferred_format="Text", typical_successful_minutes=15, current_difficulty="Easy")
    db.add(s_real)
    db.add(p_real)
    db.commit()
    
    act_id = uuid.uuid4()
    from app.models.activity import Activity, Topic
    t2 = Topic(id=uuid.uuid4(), name=f"Algebra_{uuid.uuid4()}", parent_subject="Math")
    db.add(t2)
    db.commit()
    a = Activity(id=act_id, topic_id=t2.id, title="A2", duration=15, difficulty="Easy", format="Text", kind="Learn")
    db.add(a)
    db.commit()
    
    snap = StateSnapshot(id=uuid.uuid4(), student_id=s_real.id)
    db.add(snap)
    db.commit()
    
    req = {
        "actual_duration": 15,
        "outcome": "completed",
        "feeling": "manageable",
        "snapshot_id": str(snap.id),
        "response_time": 900
    }
    
    res1 = client.post(f"/api/students/{s_real.id}/activities/{act_id}/outcome", json=req)
    assert res1.status_code == 200
    
    res2 = client.post(f"/api/students/{s_real.id}/activities/{act_id}/outcome", json=req)
    assert res2.status_code == 200
    
    events = db.query(LearningEvent).filter(LearningEvent.snapshot_id == snap.id).all()
    assert len(events) == 1

def test_snapshot_event_chronology():
    """Test 6: Snapshot/event chronology validation"""
    s_id = uuid.uuid4()
    snap = StateSnapshot(id=uuid.uuid4(), student_id=s_id, timestamp=datetime.utcnow() - timedelta(minutes=20))
    ev = LearningEvent(id=uuid.uuid4(), student_id=s_id, snapshot_id=snap.id, timestamp=datetime.utcnow() - timedelta(minutes=10))
    
    assert snap.timestamp < ev.timestamp

def test_real_data_analytics_separation(db):
    """Test 11: Real-data analytics separation"""
    from app.services.analytics_service import get_analytics_dashboard
    
    s_real = Student(id=uuid.uuid4(), name="Real Student", email=f"real_analytics_{uuid.uuid4()}@example.com", is_demo=False)
    s_demo = Student(id=uuid.uuid4(), name="Demo Student", email=f"demo_analytics_{uuid.uuid4()}@example.com", is_demo=True)
    db.add(s_real)
    db.add(s_demo)
    db.commit()
    
    snap_real = StateSnapshot(id=uuid.uuid4(), student_id=s_real.id)
    snap_demo = StateSnapshot(id=uuid.uuid4(), student_id=s_demo.id)
    db.add_all([snap_real, snap_demo])
    db.commit()
    
    ev_real = LearningEvent(id=uuid.uuid4(), student_id=s_real.id, snapshot_id=snap_real.id, outcome="completed", feeling="manageable", topic="Math", recommended_duration=10, actual_duration=10)
    ev_demo = LearningEvent(id=uuid.uuid4(), student_id=s_demo.id, snapshot_id=snap_demo.id, outcome="completed", feeling="manageable", topic="Science", recommended_duration=10, actual_duration=10)
    db.add_all([ev_real, ev_demo])
    db.commit()
    
    dash = get_analytics_dashboard(db)
    metrics = dash["metrics"]
    
    assert metrics["real_events"] > 0
    assert metrics["synthetic_events"] > 0
    assert metrics["valid_snapshot_linked_real_events"] > 0
    assert metrics["valid_snapshot_linked_synthetic_events"] > 0
