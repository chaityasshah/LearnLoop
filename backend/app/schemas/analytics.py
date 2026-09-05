from pydantic import BaseModel
from typing import Dict, Any

class AnalyticsMetrics(BaseModel):
    total_sessions: int
    completed_sessions: int
    partial_sessions: int
    abandoned_sessions: int
    completion_rate: float
    avg_recommended_duration: float
    avg_actual_duration: float
    help_request_frequency: float
    difficulty_distribution: Dict[str, int]
    format_distribution: Dict[str, int]
    consecutive_struggles_active: int
    revision_recovery_occurrences: int
    ml_ready_events: int
    events_with_valid_snapshot: int

class AnalyticsIntegrityChecks(BaseModel):
    events_without_snapshot: int
    snapshots_without_outcomes: int
    duplicate_outcome_submissions: int
    events_missing_invalid_features: int
    future_data_leakage_detected: bool

class AnalyticsDashboardResponse(BaseModel):
    metrics: AnalyticsMetrics
    integrity_checks: AnalyticsIntegrityChecks
