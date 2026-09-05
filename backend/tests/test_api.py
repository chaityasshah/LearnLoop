import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.base import Base

# We use an in-memory SQLite DB for tests so they run regardless of Postgres presence
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
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)

def test_create_student():
    import uuid
    unique_email = f"test_{uuid.uuid4()}@learnloop.local"
    response = client.post("/api/students/", json={"name": "Test User", "email": unique_email})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
    assert "id" in data
    return data["id"]

def test_get_student():
    student_id = test_create_student()
    response = client.get(f"/api/students/{student_id}")
    assert response.status_code == 200
    assert response.json()["id"] == student_id

def test_profile_flow():
    student_id = test_create_student()
    from app.models.student import LearningProfile
    import uuid
    
    db = TestingSessionLocal()
    profile = LearningProfile(
        student_id=uuid.UUID(student_id),
        preferred_format="Visual",
        typical_successful_minutes=15,
        current_difficulty="Intermediate",
        available_minutes=30
    )
    db.add(profile)
    db.commit()
    db.close()
    
    # Get Profile
    response = client.get(f"/api/students/{student_id}/profile")
    assert response.status_code == 200
    assert response.json()["typical_successful_minutes"] == 15
    
    # Update Profile
    response = client.patch(f"/api/students/{student_id}/profile", json={
        "available_minutes": 25,
        "current_difficulty": "Challenging"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["available_minutes"] == 25
    assert data["current_difficulty"] == "Challenging"
    assert data["typical_successful_minutes"] == 15

def test_help_request():
    student_id = test_create_student()
    import uuid
    dummy_activity_id = str(uuid.uuid4())
    
    response = client.post(f"/api/students/{student_id}/help-request", json={
        "activity_id": dummy_activity_id,
        "context": "I don't understand the denominator."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["context"] == "I don't understand the denominator."
    assert data["resolved"] is False

def test_activities():
    response = client.get("/api/activities/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_history():
    student_id = test_create_student()
    response = client.get(f"/api/students/{student_id}/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
