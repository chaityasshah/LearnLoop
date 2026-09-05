from app.services.adaptive_engine import generate_recommendation
from app.schemas.enums import Difficulty, Format, ActivityKind, Outcome, Feeling

class DomainProfile:
    def __init__(self, db_profile):
        self.student_id = db_profile.student_id
        self.preferred_format = Format(db_profile.preferred_format) if db_profile.preferred_format else Format.Text
        self.typical_successful_minutes = db_profile.typical_successful_minutes or 25
        self.current_difficulty = Difficulty(db_profile.current_difficulty) if db_profile.current_difficulty else Difficulty.Intermediate
        self.available_minutes = db_profile.available_minutes or 0
        
        # In a real app we'd map these JSON arrays if they existed in DB
        self.repeated_mistakes = getattr(db_profile, "repeated_mistakes", [])
        self.revision_topics = getattr(db_profile, "revision_topics", [])
        
        self.recent_completion_rate = getattr(db_profile, "recent_completion_rate", 80)
        self.completed_today = getattr(db_profile, "completed_today", 0)
        self.explanation_requests = getattr(db_profile, "explanation_requests", 0)
        self.long_activity_abandoned = db_profile.long_activity_abandoned

class DomainActivity:
    def __init__(self, db_activity):
        self.id = db_activity.id
        self.topic = db_activity.topic.name if hasattr(db_activity.topic, "name") else str(db_activity.topic)
        self.title = db_activity.title
        self.duration = db_activity.duration
        self.difficulty = Difficulty(db_activity.difficulty)
        self.format = Format(db_activity.format)
        self.kind = ActivityKind(db_activity.kind)
        self.priority = getattr(db_activity, "priority", 80)

class DomainEvent:
    def __init__(self, db_event):
        self.id = db_event.id
        self.activity_id = db_event.activity_id
        self.topic = db_event.topic
        self.actual_duration = db_event.actual_duration
        self.outcome = Outcome(db_event.outcome)
        self.feeling = Feeling(db_event.feeling)

def get_recommendation_for_student(db_activities, db_profile, db_history):
    profile = DomainProfile(db_profile)
    activities = [DomainActivity(a) for a in db_activities]
    history = [DomainEvent(e) for e in db_history]
    
    return generate_recommendation(activities, profile, history)
