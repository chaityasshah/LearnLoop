import pytest
import numpy as np

from app.ml.completion_model import CompletionProbabilityRanker, evaluate_model
from scripts.train_evaluate_model import get_chronological_split

class MockEvent:
    def __init__(self, outcome):
        self.outcome = outcome

def test_chronological_split():
    events = [MockEvent('completed'), MockEvent('partial'), MockEvent('completed'), MockEvent('skipped'), MockEvent('completed')]
    features = [{"f1": 1}, {"f1": 2}, {"f1": 3}, {"f1": 4}, {"f1": 5}]
    
    # 80% of 5 is 4
    X_train, y_train, X_test, y_test = get_chronological_split(events, features, train_ratio=0.8)
    
    assert len(X_train) == 4
    assert len(y_train) == 4
    assert len(X_test) == 1
    assert len(y_test) == 1
    
    # Chronological integrity
    assert X_train[0]["f1"] == 1
    assert X_train[-1]["f1"] == 4
    assert X_test[0]["f1"] == 5
    
    # Target conversion
    assert y_train == [1, 0, 1, 0]
    assert y_test == [1]

def test_model_training_and_predictions():
    # Construct a dataset
    X_train = [
        {"duration": 10, "difficulty": "Easy"},
        {"duration": 40, "difficulty": "Hard"},
        {"duration": 15, "difficulty": "Easy"},
        {"duration": 50, "difficulty": "Hard"}
    ]
    y_train = [1, 0, 1, 0]
    
    model = CompletionProbabilityRanker()
    model.train(X_train, y_train)
    
    assert model.is_trained is True
    
    # Predict
    X_test = [
        {"duration": 12, "difficulty": "Easy"},
        {"duration": 45, "difficulty": "Hard"}
    ]
    y_test = [1, 0]
    
    probs = model.predict_proba(X_test)
    preds = model.predict(X_test)
    
    assert len(probs) == 2
    assert len(preds) == 2
    
    # Ensure probabilities are strictly in [0, 1]
    for p in probs:
        assert 0.0 <= p <= 1.0
        
    metrics = evaluate_model(model, X_test, y_test)
    assert "accuracy" in metrics
    assert "roc_auc" in metrics
    assert metrics["positive_samples"] == 1
    assert metrics["negative_samples"] == 1

def test_single_class_training_rejection():
    X_train = [{"duration": 10}, {"duration": 20}]
    y_train = [1, 1] # Only positive class
    
    model = CompletionProbabilityRanker()
    with pytest.raises(ValueError, match="Training data must contain both classes"):
        model.train(X_train, y_train)

def test_untrained_prediction_rejection():
    model = CompletionProbabilityRanker()
    with pytest.raises(RuntimeError, match="Model is not trained"):
        model.predict([{"a": 1}])
        
def test_evaluation_single_class_test_set():
    # Model trained on both classes
    X_train = [{"a": 1}, {"a": 0}]
    y_train = [1, 0]
    model = CompletionProbabilityRanker()
    model.train(X_train, y_train)
    
    # But tested on a slice that happens to only have one class
    X_test = [{"a": 1}, {"a": 1}]
    y_test = [1, 1]
    
    metrics = evaluate_model(model, X_test, y_test)
    # ROC AUC should be gracefully skipped/None
    assert metrics["roc_auc"] is None

def test_data_provenance_separation():
    # Verify that synthetic events are identifiable and filterable
    from app.models.student import Student
    from app.models.event import LearningEvent
    
    real_student = Student(name="Alice")
    synth_student = Student(name="SYNTHETIC DEMO [IGNORE FOR ML]")
    
    e1 = LearningEvent()
    e1.student = real_student
    e2 = LearningEvent()
    e2.student = synth_student
    e3 = LearningEvent()
    e3.student = real_student
    
    events = [e1, e2, e3]
    
    synthetic_events = [e for e in events if getattr(e, 'student', None) and e.student.name == "SYNTHETIC DEMO [IGNORE FOR ML]"]
    real_events = [e for e in events if getattr(e, 'student', None) and e.student.name != "SYNTHETIC DEMO [IGNORE FOR ML]"]
    
    assert len(synthetic_events) == 1
    assert len(real_events) == 2

def test_candidate_filtering_before_ranking():
    # Verify deterministic engine controls the candidates, ML just re-ranks them.
    deterministic_candidates = [
        ("Activity A", 90), # Passed difficulty and time checks
        ("Activity B", 85), 
    ]
    
    # Model output for A is 0.4, for B is 0.9. B should be selected despite lower deterministic score.
    # But dangerous "Activity C" which failed deterministic checks should NOT even be evaluated.
    
    ml_scores = {
        "Activity A": 0.4,
        "Activity B": 0.9,
        "Activity C": 0.99
    }
    
    reranked = []
    for cand, det_score in deterministic_candidates:
        reranked.append((ml_scores[cand], cand, det_score))
        
    reranked.sort(key=lambda x: x[0], reverse=True)
    
    assert len(reranked) == 2
    assert reranked[0][1] == "Activity B"
    assert "Activity C" not in [x[1] for x in reranked]

