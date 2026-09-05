import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.models.event import LearningEvent

def evaluate_baseline():
    db = SessionLocal()
    try:
        events = db.query(LearningEvent).order_by(LearningEvent.timestamp.asc()).all()
        
        if not events:
            print("No real historical data available for baseline evaluation.")
            return
            
        total_events = len(events)
        completions = sum(1 for e in events if e.outcome == "completed")
        partials = sum(1 for e in events if e.outcome == "partial")
        skipped = sum(1 for e in events if e.outcome == "skipped")
        help_requests = sum(1 for e in events if e.help_requested)
        
        avg_rec_duration = sum(e.recommended_duration for e in events) / total_events if total_events else 0
        avg_act_duration = sum(e.actual_duration for e in events) / total_events if total_events else 0
        
        # Calculate success after struggle
        # A struggle is partial, skipped, or feeling difficult.
        # Success after struggle is when a struggle is immediately followed by a completion in the same topic.
        struggle_topics_for_student = {} # student_id -> set of topics currently struggling
        recoveries = 0
        struggle_opportunities = 0
        
        for e in events:
            sid = e.student_id
            if sid not in struggle_topics_for_student:
                struggle_topics_for_student[sid] = set()
                
            is_struggle = e.outcome in ["partial", "skipped"] or e.feeling == "difficult"
            
            if e.topic in struggle_topics_for_student[sid]:
                struggle_opportunities += 1
                if e.outcome == "completed":
                    recoveries += 1
                    struggle_topics_for_student[sid].remove(e.topic)
                    
            if is_struggle:
                struggle_topics_for_student[sid].add(e.topic)
        
        print("==================================================")
        print("DETERMINISTIC ADAPTIVE ENGINE - BASELINE EVALUATION")
        print("==================================================")
        print(f"Total Historical Events: {total_events}")
        print(f"1. Completion Rate: {completions / total_events:.2%}")
        print(f"2. Partial/Abandonment Rate: {(partials + skipped) / total_events:.2%}")
        if struggle_opportunities > 0:
            print(f"3. Success after struggle/revision: {recoveries / struggle_opportunities:.2%} ({recoveries}/{struggle_opportunities})")
        else:
            print("3. Success after struggle/revision: N/A (no struggles recorded)")
        print(f"4. Help-Request Frequency: {help_requests / total_events:.2%}")
        print(f"5. Average Recommended Duration: {avg_rec_duration:.1f} mins")
        print(f"6. Average Actual Duration: {avg_act_duration:.1f} mins")
        print("7. Recovery after repeated struggles: Insufficient data to measure 'repeated' struggles confidently.")
        
        if total_events < 50:
            print("\nWARNING: The current database does not contain enough real historical data for statistically meaningful results. A minimum of 50-100 events is recommended before interpreting baseline metrics.")
            
    finally:
        db.close()

if __name__ == "__main__":
    evaluate_baseline()
