import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import SessionLocal
from app.services.analytics_service import get_analytics_dashboard
from app.config import APP_ENV, ML_ENABLED

def run_readiness_check():
    print("==================================================")
    print("REAL DATA READINESS REPORT")
    print("==================================================")
    
    db = SessionLocal()
    try:
        analytics = get_analytics_dashboard(db)
        metrics = analytics["metrics"]
        integrity = analytics["integrity_checks"]
        
        total_real_events = metrics["real_events"]
        valid_real_events = metrics["valid_snapshot_linked_real_events"]
        invalid_real_events = total_real_events - valid_real_events
        
        # Real data completion distribution is not fully isolated in the dashboard endpoint right now 
        # (the dashboard returns overall stats). So we compute it manually here for the real dataset.
        from app.models.event import LearningEvent
        from app.models.student import Student
        real_students = db.query(Student).filter(Student.is_demo == False).all()
        real_student_ids = {s.id for s in real_students}
        
        real_events_query = db.query(LearningEvent).filter(LearningEvent.student_id.in_(real_student_ids)).all()
        real_completed = sum(1 for e in real_events_query if e.outcome == 'completed')
        
        print(f"Total Real Students: {len(real_students)}")
        print(f"Total Real Events: {total_real_events}")
        print(f"Valid Snapshot-Linked Real Events: {valid_real_events}")
        print(f"Invalid Real Events (No Snapshot): {invalid_real_events}")
        print(f"Real Events Usable for ML: {valid_real_events}")
        
        if total_real_events > 0:
            print(f"Current Real-Data Completion Rate: {real_completed / total_real_events:.2f}")
        else:
            print("Current Real-Data Completion Rate: N/A (No data)")
            
        print("\nINTEGRITY CHECKS:")
        for k, v in integrity.items():
            print(f"  - {k}: {v}")
            
        print(f"\nCurrent APP_ENV: {APP_ENV.upper()}")
        print(f"Current ML_ENABLED: {ML_ENABLED}")
        
        print("\nSTATUS:")
        if valid_real_events < 50:
            print("ML NOT READY (Requires at least 50 valid snapshot-linked real events)")
        else:
            if not ML_ENABLED:
                print("ML READY FOR EVALUATION (Enough data exists, but ML is currently disabled)")
            else:
                print("ML ENABLED (Warning: ensure safety validation is passed)")

    finally:
        db.close()

if __name__ == "__main__":
    run_readiness_check()
