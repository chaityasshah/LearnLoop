import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db, DATABASE_URL
from app.models.base import Base

# We are testing against REAL PostgreSQL using the configured DATABASE_URL
engine = create_engine(DATABASE_URL)
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
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        pytest.skip(f"PostgreSQL not available or bad credentials: {e}")
    yield
    # We do not drop_all here because it's the real development database
    app.dependency_overrides.clear()

client = TestClient(app)

def test_full_postgres_flow():
    # 1. Create Student
    import uuid
    unique_email = f"pgtest_{uuid.uuid4()}@learnloop.local"
    response = client.post("/api/students/", json={"name": "PG Test User", "email": unique_email})
    assert response.status_code == 200
    student = response.json()
    student_id = student["id"]
    
    # 2. Get Student
    response = client.get(f"/api/students/{student_id}")
    assert response.status_code == 200
    assert response.json()["email"] == unique_email

    # 3. Create Learning Profile (Manually through DB for test setup since we don't have a POST endpoint for it)
    from app.models.student import LearningProfile
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
    
    # 4. Get Profile
    response = client.get(f"/api/students/{student_id}/profile")
    assert response.status_code == 200
    assert response.json()["typical_successful_minutes"] == 15
    
    # 5. Update Profile
    response = client.patch(f"/api/students/{student_id}/profile", json={
        "current_difficulty": "Challenging"
    })
    assert response.status_code == 200
    assert response.json()["current_difficulty"] == "Challenging"
    
    # 6. Activities List
    response = client.get("/api/activities/")
    assert response.status_code == 200
    
    # 7. Get History
    response = client.get(f"/api/students/{student_id}/history")
    assert response.status_code == 200
    
    # 8. Create Help Request
    dummy_activity_id = str(uuid.uuid4())
    response = client.post(f"/api/students/{student_id}/help-request", json={
        "activity_id": dummy_activity_id,
        "context": "PG test help"
    })
    assert response.status_code == 200
    assert response.json()["context"] == "PG test help"
