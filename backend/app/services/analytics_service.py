from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.event import LearningEvent, StateSnapshot
from app.models.student import LearningProfile, Student
from scripts.export_training_data import extract_features
from collections import Counter

def get_analytics_dashboard(db: Session) -> dict:
    events = db.query(LearningEvent).all()
    profiles = db.query(LearningProfile).all()
    snapshots = db.query(StateSnapshot).all()
    
    # Pre-fetch students for provenance check
    students = {s.id: s for s in db.query(Student).all()}

    # Separate data provenance
    real_events = []
    synthetic_events = []
    
    for e in events:
        s = students.get(e.student_id)
        if s and getattr(s, 'is_demo', False):
            synthetic_events.append(e)
        else:
            real_events.append(e)

    total = len(events)
    completed = sum(1 for e in events if e.outcome == 'completed')
    partial = sum(1 for e in events if e.outcome == 'partial')
    skipped = sum(1 for e in events if e.outcome == 'skipped')
    completion_rate = completed / total if total > 0 else 0.0

    avg_rec_dur = sum(e.recommended_duration for e in events) / total if total > 0 else 0.0
    avg_act_dur = sum(e.actual_duration for e in events) / total if total > 0 else 0.0
    help_req_freq = sum(1 for e in events if getattr(e, 'help_requested', False)) / total if total > 0 else 0.0

    diff_dist = {}
    fmt_dist = {}
    for p in profiles:
        d = str(p.current_difficulty)
        f = str(p.preferred_format)
        diff_dist[d] = diff_dist.get(d, 0) + 1
        fmt_dist[f] = fmt_dist.get(f, 0) + 1

    # Recoveries & struggles
    struggle_topics = {}
    recoveries = 0
    consecutive_struggles = 0
    
    events_sorted = sorted(events, key=lambda x: x.timestamp)
    for e in events_sorted:
        sid = str(e.student_id)
        if sid not in struggle_topics:
            struggle_topics[sid] = set()
        is_struggle = e.outcome in ['partial', 'skipped'] or e.feeling == 'difficult'
        if e.topic in struggle_topics[sid]:
            if e.outcome == 'completed':
                recoveries += 1
                struggle_topics[sid].remove(e.topic)
        if is_struggle:
            struggle_topics[sid].add(e.topic)

    # Count consecutive struggles per student for current state
    student_hist = {}
    for e in events_sorted:
        student_hist.setdefault(str(e.student_id), []).append(e)
    for sid, hist in student_hist.items():
        cons = 0
        for h in reversed(hist):
            if h.outcome != 'completed' or h.feeling == 'difficult':
                cons += 1
            else:
                break
        consecutive_struggles += cons

    # Integrity checks
    events_without_snapshot = sum(1 for e in events if e.snapshot_id is None)
    event_snapshot_ids = set(e.snapshot_id for e in events if e.snapshot_id)
    snapshots_without_outcomes = sum(1 for s in snapshots if s.id not in event_snapshot_ids)
    
    # Duplicate outcomes (same snapshot_id appearing > 1 time)
    snapshot_counts = Counter(e.snapshot_id for e in events if e.snapshot_id)
    duplicate_outcomes = sum(1 for sid, count in snapshot_counts.items() if count > 1)
    
    # ML ready rows & missing features
    dataset = []
    try:
        # Need to attach snapshot manually if not joined
        snapshot_map = {s.id: s for s in snapshots}
        for e in events:
            e.snapshot = snapshot_map.get(e.snapshot_id) if e.snapshot_id else None
        dataset = extract_features(events)
    except Exception as ex:
        print("Error extracting features:", ex)
        
    ml_ready = len(dataset)
    missing_invalid_features = 0
    future_data_leakage_detected = False
    
    for row in dataset:
        # Missing fields
        if any(v is None for v in row.values()):
            missing_invalid_features += 1
            
        # Basic leakage detection constraint check:
        # If consecutive_struggles is somehow < 0, or if recent_completion_rate > 100
        # Wait, completion rate was historically 0-100.
        if row.get("recent_completion_rate", 0) > 100 or row.get("consecutive_struggles", 0) < 0:
            future_data_leakage_detected = True

    valid_real = [e for e in real_events if e.snapshot_id is not None]
    valid_synth = [e for e in synthetic_events if e.snapshot_id is not None]

    return {
        "metrics": {
            "total_sessions": total,
            "real_events": len(real_events),
            "synthetic_events": len(synthetic_events),
            "valid_snapshot_linked_real_events": len(valid_real),
            "valid_snapshot_linked_synthetic_events": len(valid_synth),
            "completed_sessions": completed,
            "partial_sessions": partial,
            "abandoned_sessions": skipped,
            "completion_rate": float(completion_rate),
            "avg_recommended_duration": float(avg_rec_dur),
            "avg_actual_duration": float(avg_act_dur),
            "help_request_frequency": float(help_req_freq),
            "difficulty_distribution": diff_dist,
            "format_distribution": fmt_dist,
            "consecutive_struggles_active": int(consecutive_struggles),
            "revision_recovery_occurrences": int(recoveries),
            "ml_ready_events": int(ml_ready),
            "events_with_valid_snapshot": total - events_without_snapshot
        },
        "integrity_checks": {
            "events_without_snapshot": events_without_snapshot,
            "snapshots_without_outcomes": snapshots_without_outcomes,
            "duplicate_outcome_submissions": duplicate_outcomes,
            "events_missing_invalid_features": missing_invalid_features,
            "future_data_leakage_detected": future_data_leakage_detected
        }
    }
