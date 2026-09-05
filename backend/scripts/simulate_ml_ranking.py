import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.student import LearningProfile, Student
from app.models.event import LearningEvent, StateSnapshot
from app.models.activity import Activity
from app.services.adaptive_engine import analyze_learning_state, calculate_task_priority, recommend_difficulty, recommend_learning_format, ActivityKind
from app.ml.completion_model import CompletionProbabilityRanker
from scripts.export_training_data import extract_features
from scripts.train_evaluate_model import get_chronological_split

def run_simulation():
    print("Connecting to DB for Offline Candidate Ranking Simulation...")
    db = SessionLocal()
    
    try:
        students = {s.id: s for s in db.query(Student).all()}
        valid_events = db.query(LearningEvent).outerjoin(StateSnapshot, LearningEvent.snapshot_id == StateSnapshot.id).filter(LearningEvent.snapshot_id != None).all()
        
        # Sort chronologically
        valid_events.sort(key=lambda x: x.timestamp)
        
        snapshots = {s.id: s for s in db.query(StateSnapshot).all()}
        for e in valid_events:
            e.snapshot = snapshots.get(e.snapshot_id)
            
        print(f"Loaded {len(valid_events)} snapshot-linked events.")
        
        # We need a trained model for simulation
        features = extract_features(valid_events)
        
        if len(valid_events) < 50:
            print("Not enough data to train the model for simulation.")
            return
            
        # We train on the first 80%, and simulate ranking for the last few events in the test set.
        X_train, y_train, X_test, y_test = get_chronological_split(valid_events, features, train_ratio=0.8)
        
        if len(set(y_train)) < 2:
            print("Training data lacks both classes.")
            return
            
        model = CompletionProbabilityRanker()
        model.train(X_train, y_train)
        print("Model trained successfully.")
        
        # Let's simulate candidate ranking for the very last test event's student BEFORE they took the event
        test_event = valid_events[-1]
        student_id = test_event.student_id
        
        profile = db.query(LearningProfile).filter(LearningProfile.student_id == student_id).first()
        history = db.query(LearningEvent).filter(LearningEvent.student_id == student_id, LearningEvent.timestamp < test_event.timestamp).order_by(LearningEvent.timestamp.asc()).all()
        
        # Deterministic Candidate Pool Filter
        print(f"\n--- Offline Candidate Ranking Simulation ---")
        print(f"Student: {student_id}")
        
        activities = db.query(Activity).all()
        state = analyze_learning_state(profile, history)
        
        scored_candidates = []
        for a in activities:
            s = calculate_task_priority(a, profile, history, state)
            scored_candidates.append((s, a))
            
        # Sort by deterministic score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Suppose the deterministic engine considers anything with score > -100 as "eligible" and safety-checked
        # Let's take the top 5 eligible candidates
        eligible_candidates = [c for c in scored_candidates if c[0] > -100][:5]
        
        print("\nDeterministic Engine Candidates (Top 5):")
        for score, act in eligible_candidates:
            topic_str = act.topic if isinstance(act.topic, str) else (act.topic.name if hasattr(act.topic, "name") else str(act.topic))
            print(f" - [{topic_str}] {act.title} (Duration: {act.duration}, Difficulty: {act.difficulty.value if hasattr(act.difficulty, 'value') else act.difficulty}) -> Deterministic Score: {score}")
            
        print("\nNow Re-ranking eligible candidates using the ML Completion Model...")
        ml_scored = []
        
        # We need to construct a snapshot context equivalent to what would be passed to extract_features
        # But wait, extract_features expects a valid LearningEvent + Snapshot. 
        # For prediction, we just need the dictionary that extract_features generates.
        # We can construct a mock event to feed to extract_features for each candidate.
        for score, act in eligible_candidates:
            # Ensure topic name exists
            topic_str = act.topic if isinstance(act.topic, str) else (act.topic.name if hasattr(act.topic, "name") else str(act.topic))
            
            mock_event = LearningEvent(
                student_id=student_id,
                activity_id=act.id,
                topic=topic_str,
                recommended_duration=act.duration,
                difficulty=act.difficulty.value if hasattr(act.difficulty, "value") else act.difficulty,
                format=act.format.value if hasattr(act.format, "value") else act.format
            )
            # The snapshot encapsulates state BEFORE the event
            mock_snapshot = StateSnapshot(
                student_id=student_id,
                available_minutes=profile.available_minutes,
                current_difficulty=profile.current_difficulty,
                typical_successful_minutes=profile.typical_successful_minutes,
                recommendation_score=score
            )
            mock_event.snapshot = mock_snapshot
            
            # For history context, extract_features expects the full chronological list up to this event
            from datetime import datetime
            mock_event.timestamp = datetime.utcnow()
            
            # Pass all history + this mock event
            cand_features_list = extract_features(history + [mock_event])
            
            # The features for the mock event is the last one in the list
            if cand_features_list:
                cand_features = cand_features_list[-1]
                prob = model.predict_proba([cand_features])[0]
                ml_scored.append((prob, score, act))
                
        ml_scored.sort(key=lambda x: x[0], reverse=True)
        
        print("\nML Re-Ranked Candidates (Safety constraints preserved!):")
        for prob, d_score, act in ml_scored:
            topic_str = act.topic if isinstance(act.topic, str) else (act.topic.name if hasattr(act.topic, "name") else str(act.topic))
            print(f" - P(Completion) = {prob:.2%}, Det. Score = {d_score} | [{topic_str}] {act.title}")
            
    except Exception as e:
        print(f"Simulation failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_simulation()
