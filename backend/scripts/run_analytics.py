import sys
import os
import json

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.services.analytics_service import get_analytics_dashboard

def run():
    print("Connecting to PostgreSQL database to run analytics...")
    db = SessionLocal()
    try:
        dashboard = get_analytics_dashboard(db)
        print("\n=== LEARNLOOP ANALYTICS DASHBOARD ===")
        print(json.dumps(dashboard, indent=2))
        
        # Additional summary
        metrics = dashboard["metrics"]
        integrity = dashboard["integrity_checks"]
        
        print("\n--- Summary ---")
        print(f"Total ML-Ready Events: {metrics['ml_ready_events']}")
        
        if integrity["future_data_leakage_detected"]:
            print("[WARNING] Future data leakage detected in the dataset!")
        else:
            print("[OK] No obvious future-data leakage detected.")
            
        if integrity["events_without_snapshot"] > 0:
            print(f"[WARNING] {integrity['events_without_snapshot']} events missing a StateSnapshot.")
            
    except Exception as e:
        print(f"Failed to run analytics: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
