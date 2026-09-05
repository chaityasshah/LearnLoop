import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models.event import LearningEvent, StateSnapshot
from scripts.generate_demo_journeys import generate_demo_journeys

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
        name="Chemistry",
        parent_subject="Science"
    )
    db.add(topic)
    
    act1 = Activity(
        id=uuid.uuid4(),
        topic_id=topic.id,
        title="Intro to Atoms",
        duration=10,
        difficulty="Easy",
        format="Visual",
        kind="Learn"
    )
    act2 = Activity(
        id=uuid.uuid4(),
        topic_id=topic.id,
        title="Advanced Atoms",
        duration=15,
        difficulty="Intermediate",
        format="Text",
        kind="Learn"
    )
    db.add_all([act1, act2])
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def test_demo_generation_invariants():
    client = TestClient(app)
    
    # Generate 5 realistic journeys completely through the API
    success = generate_demo_journeys(client=client, num_events=5)
    assert success is True
    
    db = TestingSessionLocal()
    events = db.query(LearningEvent).all()
    # Get the student ID from the events
    student_id = events[0].student_id
    snapshots = db.query(StateSnapshot).filter(StateSnapshot.student_id == student_id).all()
    
    # Check 1: Appropriate count generated
    assert len(events) == 5
    assert len(snapshots) == 6
    
    # Check 2: Every event securely linked to a valid StateSnapshot
    for event in events:
        assert event.snapshot_id is not None
        matching_snapshot = next((s for s in snapshots if str(s.id) == str(event.snapshot_id)), None)
        assert matching_snapshot is not None
        
    # Check 3: Feature extraction logic perfectly extracts these generated rows without leakage
    from scripts.export_training_data import extract_features
    # Outer join to emulate DB query layout for extraction
    joined_events = db.query(LearningEvent).outerjoin(StateSnapshot, LearningEvent.snapshot_id == StateSnapshot.id).all()
    
    snapshot_map = {s.id: s for s in snapshots}
    for je in joined_events:
        je.snapshot = snapshot_map.get(je.snapshot_id)
        
    dataset = extract_features(joined_events)
    assert len(dataset) == 5
    
    for row in dataset:
        # Check no missing fields
        assert all(v is not None for v in row.values())
        # Check invariants (like availability, rates bounded properly)
        assert row["recent_completion_rate"] <= 1.0
        assert row["consecutive_struggles"] >= 0
        
    db.close()
