import sys
import os
import json
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.event import LearningEvent, StateSnapshot
from scripts.export_training_data import extract_features
from app.ml.completion_model import CompletionProbabilityRanker, evaluate_model

def get_chronological_split(events, features, train_ratio=0.8):
    """
    Given a list of chronologically sorted events and their corresponding features,
    returns train and test sets for (X, y) without random splitting.
    """
    total = len(events)
    train_size = int(math.floor(total * train_ratio))
    
    X_train = features[:train_size]
    y_train = [1 if e.outcome == 'completed' else 0 for e in events[:train_size]]
    
    X_test = features[train_size:]
    y_test = [1 if e.outcome == 'completed' else 0 for e in events[train_size:]]
    
    return X_train, y_train, X_test, y_test

def run(real_only=False):
    print("Connecting to PostgreSQL database to fetch training data...")
    db = SessionLocal()
    try:
        from app.models.student import Student
        students = {s.id: s for s in db.query(Student).all()}
        
        # Fetch valid events (must have a snapshot)
        valid_events = db.query(LearningEvent).outerjoin(StateSnapshot, LearningEvent.snapshot_id == StateSnapshot.id).filter(LearningEvent.snapshot_id != None).all()
        
        # Chronological sort
        valid_events.sort(key=lambda x: x.timestamp)
        
        # Filter for real events if requested
        if real_only:
            valid_events = [e for e in valid_events if students.get(e.student_id) and students.get(e.student_id).name != "SYNTHETIC DEMO [IGNORE FOR ML]"]
            
        # Attach snapshot manually if needed by extract_features
        snapshots = db.query(StateSnapshot).all()
        snapshot_map = {s.id: s for s in snapshots}
        for e in valid_events:
            e.snapshot = snapshot_map.get(e.snapshot_id)
            
        dataset_type = "REAL" if real_only else "SYNTHETIC/MIXED"
        print(f"Extracted {len(valid_events)} valid snapshot-linked {dataset_type} events.")
        
        if len(valid_events) < 50:
            print(f"WARNING: Insufficient valid {dataset_type} events (<50) to train an ML model. Need more data.")
            if real_only:
                print("Skipping evaluation on real data due to insufficient samples.")
            return
            
        # Extract features ensuring NO future-data leakage
        features = extract_features(valid_events)
        
        X_train, y_train, X_test, y_test = get_chronological_split(valid_events, features, train_ratio=0.8)
        
        print(f"Chronological Split: {len(X_train)} training samples, {len(X_test)} testing samples.")
        
        # Train ML Model
        print("Training LogisticRegression candidate model...")
        model = CompletionProbabilityRanker()
        
        if len(set(y_train)) < 2:
            print(f"ERROR: Training dataset contains only one class. Cannot train binary classifier.")
            return
            
        model.train(X_train, y_train)
        
        print("Evaluating on chronologically subsequent test set...")
        metrics = evaluate_model(model, X_test, y_test)
        
        print("\n=======================================================")
        print(f"       PHASE 9/10: ML EVALUATION REPORT ({dataset_type})")
        print("=======================================================\n")
        
        print(f"Total Dataset:     {len(valid_events)} events ({dataset_type} Data)")
        print(f"Training Set:      {len(X_train)} events (Chronologically Earliest)")
        print(f"Test Set:          {len(X_test)} events (Chronologically Latest)")
        print()
        print("--- Test Set Targets ---")
        print(f"Positive (Completed):  {metrics['positive_samples']}")
        print(f"Negative (Struggled):  {metrics['negative_samples']}")
        print(f"Majority Baseline:     {metrics['majority_class_baseline']:.2%}")
        print()
        print("--- Model Performance ---")
        print(f"Accuracy:          {metrics['accuracy']:.2%}")
        print(f"Precision:         {metrics['precision']:.4f}")
        print(f"Recall:            {metrics['recall']:.4f}")
        print(f"F1 Score:          {metrics['f1']:.4f}")
        
        if metrics['roc_auc'] is not None:
            print(f"ROC-AUC:           {metrics['roc_auc']:.4f}")
        else:
            print("ROC-AUC:           N/A (Single class in test set)")
            
        print()
        print("--- Confusion Matrix ---")
        cm = metrics['confusion_matrix']
        print(f"                   Predicted Negative | Predicted Positive")
        if len(cm) == 2:
            print(f"Actual Negative  | {str(cm[0][0]).ljust(18)} | {cm[0][1]}")
            print(f"Actual Positive  | {str(cm[1][0]).ljust(18)} | {cm[1][1]}")
        else:
            print(f"Matrix: {cm}")
            
        if not real_only:
            print("\n--- Important Notice ---")
            print("CRITICAL: The current dataset is comprised of completely synthetic/demo data generated")
            print("via an automated pipeline. These metrics validate the machine learning architecture")
            print("and the strictly safe data-leakage pipeline. They do NOT represent real-world learning")
            print("improvements.")
            print("\nThe model is ready for OFFLINE experimentation only and should not be integrated")
            print("into the live recommendation decision engine until sufficient real-world data is collected.")
        else:
            print("\n--- Real-World Data Readiness ---")
            print("This evaluation was conducted strictly on authentic student interaction data.")
            print("Once metrics consistently outperform the majority baseline, this model will be")
            print("ready to rank production candidate activities safely.")
        
    except Exception as e:
        print(f"Failed to train/evaluate ML model: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    real_only = "--real-only" in sys.argv
    run(real_only=real_only)
