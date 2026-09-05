import pytest
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

def test_v1_user_journey(db):
    import uuid
    # 1. Onboarding (Create Student)
    unique_email = f"v1_user_{uuid.uuid4()}@example.com"
    res1 = client.post("/api/students/", json={"name": "V1 User", "email": unique_email})
    assert res1.status_code == 200
    student_id = res1.json()["id"]

    # 2. Check Auto-created Profile
    res2 = client.get(f"/api/students/{student_id}/profile")
    assert res2.status_code == 200
    profile = res2.json()
    assert profile["preferred_format"] == "Text"

    # 3. Create dummy activity (Setup)
    from app.models.activity import Activity, Topic
    t = Topic(id=uuid.uuid4(), name=f"E2E_{uuid.uuid4()}", parent_subject="Science")
    db.add(t)
    db.commit()
    a = Activity(id=uuid.uuid4(), topic_id=t.id, title="E2E Title", duration=15, difficulty="Easy", format="Text", kind="Learn")
    db.add(a)
    db.commit()

    # 4. Get Recommendation (Initial)
    res3 = client.get(f"/api/students/{student_id}/recommendation")
    assert res3.status_code == 200
    recommendation = res3.json()
    assert "snapshot_id" in recommendation

    # 5. Submit Outcome
    req = {
        "actual_duration": 10,
        "outcome": "completed",
        "feeling": "manageable",
        "snapshot_id": recommendation["snapshot_id"],
        "response_time": 600
    }
    res4 = client.post(f"/api/students/{student_id}/activities/{recommendation['activity']['id']}/outcome", json=req)
    assert res4.status_code == 200
    assert "event" in res4.json()
    assert "recommendation" in res4.json()

    # 6. Check History
    res5 = client.get(f"/api/students/{student_id}/history")
    assert res5.status_code == 200
    history = res5.json()
    assert len(history) == 1
    assert history[0]["outcome"] == "completed"

    # 7. Ask for Help (Study Buddy Flow)
    help_req = {
        "activity_id": recommendation["activity"]["id"],
        "context": "I don't understand the E2E topic."
    }
    res6 = client.post(f"/api/students/{student_id}/help-request", json=help_req)
    assert res6.status_code == 200

    # 8. Check Profile Updated
    res7 = client.get(f"/api/students/{student_id}/profile")
    assert res7.status_code == 200
    assert "typical_successful_minutes" in res7.json()
