import pytest
from datetime import datetime, timedelta
import uuid

from app.models.event import LearningEvent, StateSnapshot
from scripts.evaluate_real_baseline import evaluate_baseline

def create_synthetic_sequence():
    student_id = uuid.uuid4()
    activity_id = uuid.uuid4()
    
    events = []
    
    # Legacy event without snapshot (will be filtered out before evaluation, so we simulate that context)
    # The evaluation function only receives valid_events
    
    # Event 1: Completed, Medium Duration
    e1 = LearningEvent(
        student_id=student_id,
        snapshot_id=uuid.uuid4(),
        activity_id=activity_id,
        topic="Math",
        recommended_duration=15,
        actual_duration=15,
        difficulty="Easy",
        format="Visual",
        outcome="completed",
        feeling="easy",
        timestamp=datetime.utcnow() - timedelta(hours=3)
    )
    events.append(e1)
    
    # Event 2: Struggled, Short Duration
    e2 = LearningEvent(
        student_id=student_id,
        snapshot_id=uuid.uuid4(),
        activity_id=activity_id,
        topic="Math",
        recommended_duration=8,
        actual_duration=4,
        difficulty="Intermediate",
        format="Visual",
        outcome="partial",
        feeling="difficult",
        timestamp=datetime.utcnow() - timedelta(hours=2)
    )
    events.append(e2)
    
    # Event 3: Recovered, Long Duration
    e3 = LearningEvent(
        student_id=student_id,
        snapshot_id=uuid.uuid4(),
        activity_id=activity_id,
        topic="Math",
        recommended_duration=25,
        actual_duration=25,
        difficulty="Easy",
        format="Interactive",
        outcome="completed",
        feeling="manageable",
        timestamp=datetime.utcnow() - timedelta(hours=1)
    )
    events.append(e3)
    
    return events

def test_baseline_evaluation_logic():
    events = create_synthetic_sequence()
    # total events = 4 (simulating 1 legacy event that was omitted from the `events` list)
    metrics = evaluate_baseline(events, total_events_count=4)
    
    assert metrics["dataset_size"] == 4
    assert metrics["valid_samples"] == 3
    assert metrics["excluded_samples"] == 1
    
    assert metrics["overall"]["completion_rate"] == 2 / 3
    assert metrics["overall"]["partial_rate"] == 1 / 3
    assert metrics["overall"]["avg_recommended_duration"] == (15 + 8 + 25) / 3
    assert metrics["overall"]["avg_actual_duration"] == (15 + 4 + 25) / 3
    
    # Difficulty
    assert metrics["by_difficulty"]["Easy"]["completed"] == 2
    assert metrics["by_difficulty"]["Easy"]["total"] == 2
    assert metrics["by_difficulty"]["Intermediate"]["completed"] == 0
    assert metrics["by_difficulty"]["Intermediate"]["total"] == 1
    
    # Format
    assert metrics["by_format"]["Visual"]["completed"] == 1
    assert metrics["by_format"]["Interactive"]["completed"] == 1
    
    # Duration Buckets
    assert metrics["by_duration_bucket"]["Medium (10-20m)"]["total"] == 1
    assert metrics["by_duration_bucket"]["Short (<10m)"]["total"] == 1
    assert metrics["by_duration_bucket"]["Long (>20m)"]["total"] == 1
    
    assert metrics["by_duration_bucket"]["Medium (10-20m)"]["completed"] == 1
    assert metrics["by_duration_bucket"]["Short (<10m)"]["completed"] == 0
    assert metrics["by_duration_bucket"]["Long (>20m)"]["completed"] == 1

def test_recovery_chronology():
    events = create_synthetic_sequence()
    metrics = evaluate_baseline(events, 3)
    
    # The sequence was: Completed -> Struggled -> Recovered (Completed)
    # We should have exactly 1 struggle opportunity (after Event 2) and 1 recovery (Event 3).
    assert metrics["recovery"]["struggle_opportunities"] == 1
    assert metrics["recovery"]["recoveries"] == 1
    assert metrics["recovery"]["recovery_rate"] == 1.0

def test_insufficient_data_warning():
    events = create_synthetic_sequence()
    metrics = evaluate_baseline(events, 3)
    assert any("DATA INSUFFICIENT" in w for w in metrics["data_warnings"])

def test_empty_dataset():
    metrics = evaluate_baseline([], 1)
    assert metrics["valid_samples"] == 0
    assert metrics["excluded_samples"] == 1
    assert metrics["overall"]["completion_rate"] == 0.0
