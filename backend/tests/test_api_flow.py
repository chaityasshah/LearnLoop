import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
import time

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models.student import LearningProfile

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
    
    # We must seed activities for recommendations to work
    db = TestingSessionLocal()
    from app.models.activity import Activity, Topic
    
    topic = Topic(
        id=uuid.uuid4(),
        name="Fractions",
        parent_subject="Math"
    )
    db.add(topic)
    
    act = Activity(
        id=uuid.uuid4(),
        topic_id=topic.id,
        title="Intro to Fractions",
        duration=10,
        difficulty="Easy",
        format="Visual",
        kind="Learn"
    )
    db.add(act)
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)

def get_unique_email():
    return f"flow_test_{uuid.uuid4().hex[:8]}@test.local"

def test_full_remote_learning_loop():
    # 1. Create a student
    email = get_unique_email()
    res = client.post("/api/students/", json={"name": "Flow Student", "email": email})
    assert res.status_code == 200, res.text
    student_id = res.json()["id"]
    
    # Create profile manually
    db = TestingSessionLocal()
    profile = db.query(LearningProfile).filter(LearningProfile.student_id == uuid.UUID(student_id)).first()
    profile.preferred_format = "Visual"
    profile.typical_successful_minutes = 15
    profile.current_difficulty = "Easy"
    profile.available_minutes = 60
    db.commit()
    db.close()
    
    # Check initial profile
    res = client.get(f"/api/students/{student_id}/profile")
    assert res.status_code == 200
    profile = res.json()
    assert profile["current_difficulty"] == "Easy"
    assert profile["available_minutes"] == 60
    
    # Set available time restriction
    res = client.patch(f"/api/students/{student_id}/profile", json={"available_minutes": 15})
    assert res.status_code == 200
    
    # 2. Remote recommendation retrieval
    res = client.get(f"/api/students/{student_id}/recommendation")
    assert res.status_code == 200
    rec = res.json()
    
    assert "activity" in rec
    activity_id = rec["activity"]["id"]
    assert rec["duration"] <= 15
    
    # 3. Successful session
    res = client.post(
        f"/api/students/{student_id}/activities/{activity_id}/outcome",
        json={
            "actual_duration": 10,
            "outcome": "completed",
            "feeling": "easy"
        }
    )
    assert res.status_code == 200, res.text
    outcome_data = res.json()
    
    assert "event" in outcome_data, str(outcome_data)
    print("OUTCOME DATA:", outcome_data)
    event_data = outcome_data["event"]
    assert event_data.get("outcome") == "completed", str(outcome_data)
    assert event_data.get("feeling") == "easy"
    
    assert "recommendation" in outcome_data
    next_rec = outcome_data["recommendation"]
    assert "activity" in next_rec
    
    res = client.get(f"/api/students/{student_id}/profile")
    assert res.status_code == 200
    profile = res.json()
    assert profile["available_minutes"] < 15  # Should be deducted by actual_duration
    
    # 4. Struggle session
    activity_id_2 = next_rec["activity"]["id"]
    res = client.post(
        f"/api/students/{student_id}/activities/{activity_id_2}/outcome",
        json={
            "actual_duration": 5,
            "outcome": "partial",
            "feeling": "difficult"
        }
    )
    assert res.status_code == 200
    outcome_data_2 = res.json()
    
    # 5. Repeated struggle -> revision
    next_rec_2 = outcome_data_2["recommendation"]
    activity_id_3 = next_rec_2["activity"]["id"]
    res = client.post(
        f"/api/students/{student_id}/activities/{activity_id_3}/outcome",
        json={
            "actual_duration": 10,
            "outcome": "skipped",
            "feeling": "difficult"
        }
    )
    assert res.status_code == 200
    outcome_data_3 = res.json()
    
    # Check profile for revision topics
    res = client.get(f"/api/students/{student_id}/profile")
    profile = res.json()
    
    # 6. Help request -> support mode
    res = client.post(
        f"/api/students/{student_id}/help-request",
        json={
            "activity_id": activity_id_3,
            "context": "I need help"
        }
    )
    assert res.status_code == 200

def test_ml_pipeline_invariants():
    # 1. Create a student
    email = get_unique_email()
    res = client.post("/api/students/", json={"name": "ML Test Student", "email": email})
    assert res.status_code == 200, res.text
    student_id = res.json()["id"]

    db = TestingSessionLocal()
    profile = db.query(LearningProfile).filter(LearningProfile.student_id == uuid.UUID(student_id)).first()
    profile.preferred_format = "Visual"
    profile.typical_successful_minutes = 20
    profile.current_difficulty = "Intermediate"
    profile.available_minutes = 45
    db.commit()
    db.close()

    # 2. Get recommendation and verify snapshot
    res = client.get(f"/api/students/{student_id}/recommendation")
    assert res.status_code == 200
    rec = res.json()
    assert "snapshot_id" in rec
    snapshot_id_str = rec["snapshot_id"]
    snapshot_uuid = uuid.UUID(snapshot_id_str)
    activity_id = rec["activity"]["id"]

    # Check database for snapshot
    db = TestingSessionLocal()
    from app.models.event import StateSnapshot, LearningEvent
    snapshot = db.query(StateSnapshot).filter(StateSnapshot.id == snapshot_uuid).first()
    assert snapshot is not None
    assert snapshot.available_minutes == 45
    assert snapshot.current_difficulty == "Intermediate"
    assert snapshot.typical_successful_minutes == 20
    db.close()

    # 3. Post outcome with snapshot_id
    res = client.post(
        f"/api/students/{student_id}/activities/{activity_id}/outcome",
        json={
            "actual_duration": 15,
            "outcome": "completed",
            "feeling": "manageable",
            "snapshot_id": snapshot_id_str
        }
    )
    assert res.status_code == 200
    outcome_data = res.json()
    assert "event" in outcome_data

    # Check LearningEvent linkage
    db = TestingSessionLocal()
    event = db.query(LearningEvent).filter(LearningEvent.student_id == uuid.UUID(student_id)).order_by(LearningEvent.timestamp.desc()).first()
    assert event is not None
    assert str(event.snapshot_id) == snapshot_id_str
    db.close()

    # 4. Feature extraction should not leak
    from scripts.export_training_data import extract_features
    db = TestingSessionLocal()
    events = db.query(LearningEvent).outerjoin(StateSnapshot, LearningEvent.snapshot_id == StateSnapshot.id).filter(LearningEvent.student_id == uuid.UUID(student_id)).all()
    # attach snapshot
    snapshots = {s.id: s for s in db.query(StateSnapshot).all()}
    for e in events:
        e.snapshot = snapshots.get(e.snapshot_id) if e.snapshot_id else None
    
    dataset = extract_features(events)
    assert len(dataset) == 1
    row = dataset[0]
    
    # State from snapshot must match what was captured at recommendation time!
    assert row["available_minutes"] == 45
    assert row["current_difficulty"] == "Intermediate"
    assert row["typical_successful_minutes"] == 20
    
    # Profile might have changed now! Let's check it changed.
    updated_profile = db.query(LearningProfile).filter(LearningProfile.student_id == uuid.UUID(student_id)).first()
    # Deducted activity duration (10)
    assert updated_profile.available_minutes == 35 
    
    # But row contains the OLD value (45) since it uses the snapshot, confirming zero leakage
    assert row["available_minutes"] != updated_profile.available_minutes
    db.close()
