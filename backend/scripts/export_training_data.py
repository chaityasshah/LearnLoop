import os
import sys
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.models.event import LearningEvent, StateSnapshot
from app.models.activity import Activity, Topic
from sqlalchemy.orm import joinedload

def extract_features(events):
    # Sort chronologically
    events = sorted(events, key=lambda x: x.timestamp)
    
    dataset = []
    
    # State tracking per student
    student_history = {}
    
    for event in events:
        sid = event.student_id
        if sid not in student_history:
            student_history[sid] = []
            
        history = student_history[sid]
        
        # Calculate features strictly from history BEFORE this event
        total_past = len(history)
        completed_past = sum(1 for h in history if h.outcome == "completed")
        recent_events = history[-10:] if len(history) > 10 else history
        recent_completion_rate = (sum(1 for h in recent_events if h.outcome == "completed") / len(recent_events)) if recent_events else 0.8
        
        topic_history = [h for h in history if h.topic == event.topic]
        topic_success_rate = (sum(1 for h in topic_history if h.outcome == "completed") / len(topic_history)) if topic_history else 0.5
        
        recent_struggle_count = sum(1 for h in recent_events if h.feeling == "difficult" or h.outcome in ["skipped", "partial"])
        
        # Consecutive struggles overall
        consecutive_struggles = 0
        for h in reversed(history):
            if h.feeling == "difficult" or h.outcome != "completed":
                consecutive_struggles += 1
            else:
                break
                
        help_request_frequency = (sum(1 for h in history if h.help_requested) / total_past) if total_past > 0 else 0
        
        time_since_last_seen = 0
        if topic_history:
            last_seen = max(h.timestamp for h in topic_history)
            time_since_last_seen = (event.timestamp - last_seen).total_seconds() / 3600.0 # in hours
            
        # Snapshot state if available
        available_minutes = 30
        current_difficulty = "Intermediate"
        typical_successful_minutes = 15
        recommendation_score = 50
        
        if hasattr(event, 'snapshot') and event.snapshot:
            available_minutes = event.snapshot.available_minutes or available_minutes
            current_difficulty = event.snapshot.current_difficulty or current_difficulty
            typical_successful_minutes = event.snapshot.typical_successful_minutes or typical_successful_minutes
            recommendation_score = event.snapshot.recommendation_score or recommendation_score

        # Target definition: did the student successfully complete the activity?
        # Target = 1 if outcome == "completed", 0 otherwise
        target = 1 if event.outcome == "completed" else 0
        
        row = {
            "timestamp": event.timestamp.isoformat(),
            "student_id": str(event.student_id),
            "activity_id": str(event.activity_id),
            "topic": event.topic,
            "activity_duration": event.recommended_duration,
            "activity_difficulty": event.difficulty,
            "activity_format": event.format,
            
            # Features
            "recent_completion_rate": round(recent_completion_rate, 2),
            "topic_success_rate": round(topic_success_rate, 2),
            "recent_struggle_count": recent_struggle_count,
            "consecutive_struggles": consecutive_struggles,
            "help_request_frequency": round(help_request_frequency, 2),
            "time_since_last_seen_hours": round(time_since_last_seen, 2),
            
            # State from snapshot
            "available_minutes": available_minutes,
            "current_difficulty": current_difficulty,
            "typical_successful_minutes": typical_successful_minutes,
            "recommendation_score": recommendation_score,
            
            # Target
            "target_completed": target
        }
        
        dataset.append(row)
        history.append(event)
        
    return dataset

def export_training_data(output_path="training_data.csv"):
    db = SessionLocal()
    try:
        # Load all events with their snapshots
        events = db.query(LearningEvent).outerjoin(StateSnapshot, LearningEvent.snapshot_id == StateSnapshot.id).all()
        
        # We manually attach snapshot if outerjoin doesn't populate the relationship, 
        # but let's just query it safely
        snapshots = {s.id: s for s in db.query(StateSnapshot).all()}
        for e in events:
            e.snapshot = snapshots.get(e.snapshot_id) if e.snapshot_id else None
            
        dataset = extract_features(events)
        
        if not dataset:
            print("No learning events found in the database. Export skipped.")
            return
            
        headers = list(dataset[0].keys())
        
        with open(output_path, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in dataset:
                writer.writerow(row)
                
        print(f"Exported {len(dataset)} events to {output_path}")
        
    finally:
        db.close()

if __name__ == "__main__":
    export_training_data()
