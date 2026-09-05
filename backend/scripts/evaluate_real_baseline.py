import sys
import os
import json
from collections import defaultdict
from sqlalchemy.orm import Session

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.event import LearningEvent, StateSnapshot

def get_duration_bucket(duration):
    if duration < 10: return "Short (<10m)"
    if duration <= 20: return "Medium (10-20m)"
    return "Long (>20m)"

def evaluate_baseline(events, total_events_count):
    valid_samples = len(events)
    excluded = total_events_count - valid_samples
    
    metrics = {
        "dataset_size": total_events_count,
        "valid_samples": valid_samples,
        "excluded_samples": excluded,
        "overall": {
            "completion_rate": 0.0,
            "partial_rate": 0.0,
            "abandonment_rate": 0.0,
            "help_request_frequency": 0.0,
            "avg_recommended_duration": 0.0,
            "avg_actual_duration": 0.0,
        },
        "by_difficulty": defaultdict(lambda: {"total": 0, "completed": 0}),
        "by_format": defaultdict(lambda: {"total": 0, "completed": 0}),
        "by_duration_bucket": defaultdict(lambda: {"total": 0, "completed": 0}),
        "recovery": {
            "struggle_opportunities": 0,
            "recoveries": 0,
            "recovery_rate": 0.0
        },
        "data_warnings": []
    }
    
    if valid_samples < 50:
        metrics["data_warnings"].append(
            f"DATA INSUFFICIENT: Only {valid_samples} valid samples. 50+ required for statistically meaningful ML experimentation."
        )
    else:
        metrics["data_warnings"].append("DATA SUFFICIENT: Dataset size is adequate for initial ML baseline ranking.")
        
    if valid_samples == 0:
        return metrics
        
    completed = 0
    partial = 0
    abandoned = 0
    help_req = 0
    rec_dur_sum = 0
    act_dur_sum = 0
    
    # Track chronological struggle history per student for strict recovery bounds
    student_history = defaultdict(list)
    
    for e in events:
        if e.outcome == 'completed': completed += 1
        if e.outcome == 'partial': partial += 1
        if e.outcome == 'skipped': abandoned += 1
        if getattr(e, 'help_requested', False): help_req += 1
        rec_dur_sum += e.recommended_duration
        act_dur_sum += e.actual_duration
        
        metrics["by_difficulty"][e.difficulty]["total"] += 1
        if e.outcome == 'completed': metrics["by_difficulty"][e.difficulty]["completed"] += 1
            
        metrics["by_format"][e.format]["total"] += 1
        if e.outcome == 'completed': metrics["by_format"][e.format]["completed"] += 1
            
        bkt = get_duration_bucket(e.recommended_duration)
        metrics["by_duration_bucket"][bkt]["total"] += 1
        if e.outcome == 'completed': metrics["by_duration_bucket"][bkt]["completed"] += 1
            
        student_history[str(e.student_id)].append(e)
        
    metrics["overall"]["completion_rate"] = completed / valid_samples
    metrics["overall"]["partial_rate"] = partial / valid_samples
    metrics["overall"]["abandonment_rate"] = abandoned / valid_samples
    metrics["overall"]["help_request_frequency"] = help_req / valid_samples
    metrics["overall"]["avg_recommended_duration"] = rec_dur_sum / valid_samples
    metrics["overall"]["avg_actual_duration"] = act_dur_sum / valid_samples
    
    # Strict Chronological Recovery Evaluation
    for sid, hist in student_history.items():
        hist.sort(key=lambda x: x.timestamp)
        in_struggle = False
        for h in hist:
            if in_struggle:
                metrics["recovery"]["struggle_opportunities"] += 1
                if h.outcome == 'completed':
                    metrics["recovery"]["recoveries"] += 1
                    in_struggle = False # They recovered!
                elif h.outcome in ['partial', 'skipped'] or h.feeling == 'difficult':
                    pass # Remained in struggle
            else:
                if h.outcome in ['partial', 'skipped'] or h.feeling == 'difficult':
                    in_struggle = True
                    
    if metrics["recovery"]["struggle_opportunities"] > 0:
        metrics["recovery"]["recovery_rate"] = metrics["recovery"]["recoveries"] / metrics["recovery"]["struggle_opportunities"]
        
    # Convert and format rates
    for d in [metrics["by_difficulty"], metrics["by_format"], metrics["by_duration_bucket"]]:
        for k in d:
            t = d[k]["total"]
            d[k]["rate"] = d[k]["completed"] / t if t > 0 else 0.0

    metrics["by_difficulty"] = dict(metrics["by_difficulty"])
    metrics["by_format"] = dict(metrics["by_format"])
    metrics["by_duration_bucket"] = dict(metrics["by_duration_bucket"])
        
    return metrics

def run():
    print("Connecting to PostgreSQL database to establish ML Baseline...")
    db = SessionLocal()
    try:
        total_events_count = db.query(LearningEvent).count()
        valid_events = db.query(LearningEvent).outerjoin(StateSnapshot, LearningEvent.snapshot_id == StateSnapshot.id).filter(LearningEvent.snapshot_id != None).all()
        
        metrics = evaluate_baseline(valid_events, total_events_count)
        
        print("\n=======================================================")
        print("          PHASE 8C: REAL-DATA BASELINE EVALUATION      ")
        print("=======================================================\n")
        
        print(f"1. Dataset Size: {metrics['dataset_size']} total events")
        print(f"2. Valid Evaluation Samples: {metrics['valid_samples']}")
        print(f"3. Excluded Legacy Samples (No Snapshot): {metrics['excluded_samples']}\n")
        
        print("4. Overall Baseline Metrics:")
        print(f"   Completion Rate:       {metrics['overall']['completion_rate']:.2%}")
        print(f"   Partial Rate:          {metrics['overall']['partial_rate']:.2%}")
        print(f"   Abandonment Rate:      {metrics['overall']['abandonment_rate']:.2%}")
        print(f"   Help-Request Freq:     {metrics['overall']['help_request_frequency']:.2%}")
        print(f"   Avg Rec Duration:      {metrics['overall']['avg_recommended_duration']:.1f}m")
        print(f"   Avg Actual Duration:   {metrics['overall']['avg_actual_duration']:.1f}m\n")
        
        print("5. Completion Rate by Difficulty:")
        for k, v in metrics["by_difficulty"].items():
            print(f"   {k.ljust(15)}: {v['rate']:.2%} ({v['completed']}/{v['total']})")
        print()
        
        print("6. Completion Rate by Recommended Duration Bucket:")
        for k, v in metrics["by_duration_bucket"].items():
            print(f"   {k.ljust(15)}: {v['rate']:.2%} ({v['completed']}/{v['total']})")
        print()
        
        print("7. Recovery Metrics (Chronological):")
        print(f"   Struggle Sequences Identified:  {metrics['recovery']['struggle_opportunities']}")
        print(f"   Successful Recoveries:          {metrics['recovery']['recoveries']}")
        print(f"   Recovery Rate:                  {metrics['recovery']['recovery_rate']:.2%}\n")
        
        print("8. Statistical & ML Readiness Warnings:")
        for w in metrics["data_warnings"]:
            print(f"   - {w}")
            
    except Exception as e:
        print(f"Failed to evaluate baseline: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
