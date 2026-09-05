import sys
import os
import json
import uuid
from datetime import datetime
from collections import defaultdict
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.student import LearningProfile, Student
from app.models.event import LearningEvent, StateSnapshot
from app.models.activity import Activity
from app.services.adaptive_engine import analyze_learning_state, calculate_task_priority, ActivityKind
from app.ml.completion_model import CompletionProbabilityRanker
from scripts.export_training_data import extract_features

import joblib

def print_separator(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def run_experiment():
    print_separator("PHASE 12: OFFLINE ML EXPERIMENTATION")
    
    db = SessionLocal()
    
    try:
        activities = db.query(Activity).all()
        if not activities:
            print("No activities found in DB.")
            return

        students = {s.id: s for s in db.query(Student).all()}
        all_events = db.query(LearningEvent).outerjoin(StateSnapshot, LearningEvent.snapshot_id == StateSnapshot.id).filter(LearningEvent.snapshot_id != None).all()
        all_events.sort(key=lambda x: x.timestamp)
        
        snapshots = {s.id: s for s in db.query(StateSnapshot).all()}
        for e in all_events:
            e.snapshot = snapshots.get(e.snapshot_id)
            
        print(f"Loaded {len(all_events)} snapshot-linked events.")
        
        synthetic_events = []
        real_events = []
        for e in all_events:
            student = students.get(e.student_id)
            if student and "SYNTHETIC DEMO" in student.name:
                synthetic_events.append(e)
            else:
                real_events.append(e)
                
        datasets = [("SYNTHETIC", synthetic_events), ("REAL", real_events)]
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
        os.makedirs(models_dir, exist_ok=True)
        
        for name, events in datasets:
            print_separator(f"EVALUATING {name} DATASET")
            
            if len(events) < 50:
                print(f"INSUFFICIENT DATA for {name} dataset. Found {len(events)}, requires 50.")
                continue
                
            features_list = extract_features(events)
            
            split_idx = int(len(features_list) * 0.8)
            train_features = features_list[:split_idx]
            test_features = features_list[split_idx:]
            test_events = events[split_idx:]
            
            X_train = []
            y_train = []
            for f in train_features:
                x_dict = {k: v for k, v in f.items() if isinstance(v, (int, float)) and not k.endswith("id") and k != "target_completed"}
                X_train.append(x_dict)
                y_train.append(f["target_completed"])
                
            if len(set(y_train)) < 2:
                print(f"Skipping {name}: Train set lacks both completion classes.")
                continue
                
            model = CompletionProbabilityRanker()
            model.train(X_train, y_train)
            
            X_test = []
            y_test = []
            for f in test_features:
                x_dict = {k: v for k, v in f.items() if isinstance(v, (int, float)) and not k.endswith("id") and k != "target_completed"}
                X_test.append(x_dict)
                y_test.append(f["target_completed"])
                
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)
            
            from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
            
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            try:
                auc = roc_auc_score(y_test, y_prob)
            except ValueError:
                auc = -1
                
            print(f"Predictive Metrics (Chronological Test Set):")
            print(f"- Precision: {precision:.2f}")
            print(f"- Recall: {recall:.2f}")
            print(f"- F1 Score: {f1:.2f}")
            if auc >= 0:
                print(f"- ROC-AUC: {auc:.2f}")
            # Phase 12F: Model Interpretability
            print(f"\nModel Interpretability (Logistic Regression):")
            feature_names = [k for k, v in train_features[0].items() if isinstance(v, (int, float)) and not k.endswith("id") and k != "target_completed"]
            if hasattr(model, "pipeline") and "classifier" in model.pipeline.named_steps:
                classifier = model.pipeline.named_steps["classifier"]
                if hasattr(classifier, "coef_"):
                    coefs = classifier.coef_[0]
                    # Also we need to get feature names after DictVectorizer if possible
                    # But the dict vectorizer alphabetizes the keys
                    vectorizer = model.pipeline.named_steps["vectorizer"]
                    if hasattr(vectorizer, "get_feature_names_out"):
                        feature_names = vectorizer.get_feature_names_out()
                        
                    feat_importance = list(zip(feature_names, coefs))
                    feat_importance.sort(key=lambda x: abs(x[1]), reverse=True)
                    for feat, weight in feat_importance[:10]:
                        direction = "+" if weight > 0 else "-"
                        print(f"  {feat}: {weight:.4f} ({direction})")
                    print("  Note: Model identifies correlations useful for prediction; this does not infer causality.")
                
            # Phase 12G: Model Versioning
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            model_path = os.path.join(models_dir, f"{name.lower()}_model_{timestamp_str}.joblib")
            meta_path = os.path.join(models_dir, f"{name.lower()}_meta_{timestamp_str}.json")
            
            joblib.dump(model.pipeline, model_path)
            
            metadata = {
                "version": "1.0",
                "training_timestamp": timestamp_str,
                "provenance": name,
                "features": list(feature_names),
                "metrics": {
                    "precision": float(precision),
                    "recall": float(recall),
                    "f1": float(f1),
                    "roc_auc": float(auc)
                },
                "training_samples": len(X_train),
                "test_samples": len(X_test)
            }
            
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)
                
            print(f"\nOffline Policy Comparison ({len(test_events)} events):")
            
            agreements = 0
            ml_divergences = 0
            ml_selected_infeasible = 0
            
            for i, event in enumerate(test_events):
                student_id = event.student_id
                snapshot = event.snapshot
                
                class MockProfile:
                    pass
                profile = MockProfile()
                profile.student_id = student_id
                profile.available_minutes = snapshot.available_minutes or 30
                profile.current_difficulty = snapshot.current_difficulty or "Intermediate"
                profile.typical_successful_minutes = snapshot.typical_successful_minutes or 25
                profile.preferred_format = "Text"
                
                history = [h for h in events if h.student_id == student_id and h.timestamp < event.timestamp]
                state = analyze_learning_state(profile, history)
                
                scored_candidates = []
                for act in activities:
                    if act.duration > profile.available_minutes:
                        continue
                    s = calculate_task_priority(act, profile, history, state)
                    scored_candidates.append((s, act))
                    
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                if not scored_candidates:
                    continue
                    
                det_top_act = scored_candidates[0][1]
                eligible_candidates = scored_candidates[:10]
                
                ml_candidates = []
                for det_score, act in eligible_candidates:
                    topic_str = act.topic if isinstance(act.topic, str) else (act.topic.name if hasattr(act.topic, "name") else str(act.topic))
                    mock_event = LearningEvent(
                        student_id=student_id, activity_id=act.id, topic=topic_str,
                        recommended_duration=act.duration,
                        difficulty=act.difficulty.value if hasattr(act.difficulty, "value") else act.difficulty,
                        format=act.format.value if hasattr(act.format, "value") else act.format
                    )
                    mock_snapshot = StateSnapshot(
                        student_id=student_id, available_minutes=profile.available_minutes,
                        current_difficulty=profile.current_difficulty,
                        typical_successful_minutes=profile.typical_successful_minutes,
                        recommendation_score=det_score
                    )
                    mock_event.snapshot = mock_snapshot
                    mock_event.timestamp = event.timestamp
                    
                    cand_features_list = extract_features(history + [mock_event])
                    cand_feat_dict = cand_features_list[-1]
                    x_dict = {k: v for k, v in cand_feat_dict.items() if isinstance(v, (int, float)) and not k.endswith("id") and k != "target_completed"}
                    
                    prob = model.predict_proba([x_dict])[0]
                    ml_candidates.append((prob, det_score, act))
                    
                ml_candidates.sort(key=lambda x: x[0], reverse=True)
                ml_top_act = ml_candidates[0][2]
                
                if ml_top_act.id == det_top_act.id:
                    agreements += 1
                else:
                    ml_divergences += 1
                    
                if ml_top_act.duration > profile.available_minutes:
                    ml_selected_infeasible += 1
                    
            print(f"- Total Test Queries: {len(test_events)}")
            print(f"- ML agreed with Deterministic: {agreements} ({agreements/len(test_events):.1%})")
            print(f"- ML diverged safely: {ml_divergences} ({ml_divergences/len(test_events):.1%})")
            print(f"- ML selected infeasible (Safety Violation): {ml_selected_infeasible}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Experiment failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_experiment()
