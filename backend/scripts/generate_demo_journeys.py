import sys
import os
import random
import uuid
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import get_db

def generate_demo_journeys(client=None, num_events=60):
    if client is None:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        
    print(f"Generating {num_events} demo API-driven events...")
    
    email = f"demo_journey_{uuid.uuid4().hex[:6]}@example.com"
    res = client.post("/api/students/", json={"name": "SYNTHETIC DEMO [IGNORE FOR ML]", "email": email})
    if res.status_code != 200:
        print("Failed to create student:", res.text)
        return False
        
    student_id = res.json()["id"]
    
    # Configure initial profile via DB since there's no POST route
    from app.db.session import SessionLocal
    from app.models.student import LearningProfile
    
    db = SessionLocal()
    if client.app.dependency_overrides.get(get_db):
        db = next(client.app.dependency_overrides[get_db]())
        
    profile = LearningProfile(
        student_id=uuid.UUID(student_id),
        preferred_format="Visual",
        typical_successful_minutes=20,
        current_difficulty="Intermediate",
        available_minutes=200
    )
    db.add(profile)
    db.commit()
    db.close()
    
    success_count = 0
    current_rec = None
    
    for i in range(num_events):
        # 1. Recommendation Phase (Creates Snapshot)
        if current_rec is None:
            rec_res = client.get(f"/api/students/{student_id}/recommendation")
            if rec_res.status_code != 200:
                print(f"Recommendation failed: {rec_res.text}")
                break
            rec = rec_res.json()
        else:
            rec = current_rec
            
        snapshot_id = rec.get("snapshot_id")
        activity = rec.get("activity")
        
        if not snapshot_id or not activity:
            print("Missing snapshot or activity in recommendation payload.")
            break
            
        act_id = activity["id"]
        rec_duration = rec["duration"]
        
        # 2. Simulate User Behavior
        rand = random.random()
        if rand < 0.6:
            outcome = "completed"
            feeling = "manageable"
            act_dur = rec_duration
        elif rand < 0.8:
            outcome = "completed"
            feeling = "easy"
            act_dur = max(1, rec_duration - 2)
        elif rand < 0.95:
            outcome = "partial"
            feeling = "difficult"
            act_dur = max(1, rec_duration // 2)
        else:
            outcome = "skipped"
            feeling = "difficult"
            act_dur = 1
            
        # 3. Outcome Phase (Links to Snapshot, and API automatically returns next recommendation)
        out_res = client.post(
            f"/api/students/{student_id}/activities/{act_id}/outcome",
            json={
                "actual_duration": act_dur,
                "outcome": outcome,
                "feeling": feeling,
                "snapshot_id": snapshot_id
            }
        )
        
        if out_res.status_code != 200:
            print(f"Outcome submission failed: {out_res.text}")
            break
            
        out_data = out_res.json()
        current_rec = out_data.get("recommendation")
        
        success_count += 1
            
        # 4. Optional Help Request
        if feeling == "difficult" and random.random() < 0.5:
            client.post(
                f"/api/students/{student_id}/help-request",
                json={"activity_id": act_id, "context": "I don't understand this specific part."}
            )
            
        # Replenish time to avoid hitting the 0-minute cap mid-journey
        if i % 5 == 0:
            client.patch(f"/api/students/{student_id}/profile", json={
                "available_minutes": 200
            })
            
        # Guarantee strict chronological spacing
        time.sleep(0.01)
        
    print(f"Successfully generated {success_count} API-driven events for demo student {student_id}.")
    return success_count == num_events

if __name__ == "__main__":
    generate_demo_journeys(num_events=60)
