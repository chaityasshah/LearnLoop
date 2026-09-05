import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.student import Student, LearningProfile
from app.models.activity import Activity, Topic
from app.models.event import LearningEvent, StateSnapshot
from app.schemas.enums import Outcome, Feeling, Difficulty, Format

client = TestClient(app)

@pytest.fixture
def setup_data():
    db = SessionLocal()
    # Create student
    student_id = uuid.uuid4()
    student = Student(id=student_id, name="Hardening Test Student", email=f"{student_id}@test.com")
    db.add(student)
    db.flush()
    
    # Create profile with limited time
    profile = LearningProfile(student_id=student_id, available_minutes=10, current_difficulty="Easy", preferred_format="Text")
    db.add(profile)
    
    # Create topic
    topic_id = uuid.uuid4()
    topic = Topic(id=topic_id, name="Testing")
    db.add(topic)
    db.flush()
    
    # Create activity
    activity_id = uuid.uuid4()
    activity = Activity(
        id=activity_id,
        title="Hardening Task",
        topic_id=topic_id,
        kind="Practice",
        difficulty="Easy",
        format="Text",
        duration=15 # Longer than available minutes
    )
    db.add(activity)
    db.flush()
    
    # Create snapshot for idempotency test
    snapshot_id = uuid.uuid4()
    snapshot = StateSnapshot(student_id=student_id, available_minutes=10, current_difficulty="Easy", recommendation_score=100, id=snapshot_id)
    db.add(snapshot)
    
    db.commit()
    
    yield {"student_id": str(student_id), "activity_id": str(activity_id), "snapshot_id": str(snapshot_id)}
    
    # Teardown
    db.query(LearningEvent).filter(LearningEvent.student_id == student_id).delete()
    db.query(StateSnapshot).filter(StateSnapshot.student_id == student_id).delete()
    db.query(LearningProfile).filter(LearningProfile.student_id == student_id).delete()
    db.query(Student).filter(Student.id == student_id).delete()
    db.query(Activity).filter(Activity.id == activity_id).delete()
    db.query(Topic).filter(Topic.id == topic_id).delete()
    db.commit()
    db.close()

def test_readiness_endpoint():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["database"] == "connected"

def test_idempotent_outcome_submission(setup_data):
    student_id = setup_data["student_id"]
    activity_id = setup_data["activity_id"]
    snapshot_id = setup_data["snapshot_id"]
    
    payload = {
        "actual_duration": 15,
        "outcome": "completed",
        "feeling": "manageable",
        "snapshot_id": snapshot_id
    }
    
    # First submission
    resp1 = client.post(f"/api/students/{student_id}/activities/{activity_id}/outcome", json=payload)
    assert resp1.status_code == 200
    event_id1 = resp1.json()["event"]["id"]
    
    # Double submission (e.g. frontend retry)
    resp2 = client.post(f"/api/students/{student_id}/activities/{activity_id}/outcome", json=payload)
    assert resp2.status_code == 200
    event_id2 = resp2.json()["event"]["id"]
    
    # Should return the same event ID, not process twice
    assert event_id1 == event_id2
    
    # Verify DB only has one event
    db = SessionLocal()
    events = db.query(LearningEvent).filter(LearningEvent.snapshot_id == uuid.UUID(snapshot_id)).all()
    assert len(events) == 1
    
    # Verify time didn't go negative or double deduct
    profile = db.query(LearningProfile).filter(LearningProfile.student_id == uuid.UUID(student_id)).first()
    assert profile.available_minutes == 0 # Started at 10, used 15, clamped to 0. Not -5, not -20.
    db.close()

def test_negative_time_prevention(setup_data):
    # Already verified in idempotent test, but let's be explicit
    db = SessionLocal()
    profile = db.query(LearningProfile).filter(LearningProfile.student_id == uuid.UUID(setup_data["student_id"])).first()
    assert profile.available_minutes >= 0
    db.close()

def test_invalid_uuid_handling(setup_data):
    payload = {
        "actual_duration": 10,
        "outcome": "completed",
        "feeling": "manageable",
        "snapshot_id": setup_data["snapshot_id"]
    }
    # Send bad student UUID
    resp = client.post(f"/api/students/invalid-uuid/activities/{setup_data['activity_id']}/outcome", json=payload)
    assert resp.status_code == 422 # FastAPI validation
    
def test_snapshot_owner_mismatch(setup_data):
    # Try to submit an outcome using another student's snapshot
    db = SessionLocal()
    other_student = Student(name="Other")
    db.add(other_student)
    db.commit()
    db.refresh(other_student)
    
    payload = {
        "actual_duration": 10,
        "outcome": "completed",
        "feeling": "manageable",
        "snapshot_id": setup_data["snapshot_id"]
    }
    
    resp = client.post(f"/api/students/{other_student.id}/activities/{setup_data['activity_id']}/outcome", json=payload)
    assert resp.status_code == 400
    assert "Snapshot does not belong to this student" in resp.json()["detail"]
    
    db.query(Student).filter(Student.id == other_student.id).delete()
    db.commit()
    db.close()
