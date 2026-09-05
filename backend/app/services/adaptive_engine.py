from typing import List, Dict, Tuple, Any
from pydantic import BaseModel
from app.schemas.enums import Difficulty, Format, ActivityKind, Outcome, Feeling
import math

difficulty_value = {
    Difficulty.Easy: 1,
    Difficulty.Intermediate: 2,
    Difficulty.Challenging: 3,
}

def next_difficulty(d: Difficulty) -> Difficulty:
    if d == Difficulty.Easy: return Difficulty.Intermediate
    if d == Difficulty.Intermediate: return Difficulty.Challenging
    return Difficulty.Challenging

def prev_difficulty(d: Difficulty) -> Difficulty:
    if d == Difficulty.Challenging: return Difficulty.Intermediate
    if d == Difficulty.Intermediate: return Difficulty.Easy
    return Difficulty.Easy

class LearningState(BaseModel):
    needsRevision: bool
    shortSuccess: int
    longStruggle: bool
    consecutiveStruggles: int
    consecutiveSuccesses: int
    isConsistent: bool
    hasLimitedTime: bool
    topicStruggleCount: Dict[str, int]
    topicSuccessCount: Dict[str, int]
    totalExplainRequests: int
    supportModeActive: bool

def analyze_learning_state(profile, history) -> LearningState:
    recent = history[-6:] if history else []
    
    short_success = len([x for x in recent if x.actual_duration <= 15 and x.outcome == Outcome.completed and x.feeling != Feeling.difficult])
    recent_long_struggle = any(x.actual_duration > 15 and x.outcome != Outcome.completed for x in recent)
    long_struggle = getattr(profile, "long_activity_abandoned", False) or recent_long_struggle

    consecutive_struggles = 0
    for h in reversed(history):
        struggled = h.outcome != Outcome.completed or h.feeling == Feeling.difficult
        if struggled: consecutive_struggles += 1
        else: break

    consecutive_successes = 0
    for h in reversed(history):
        succeeded = h.outcome == Outcome.completed and h.feeling != Feeling.difficult
        if succeeded: consecutive_successes += 1
        else: break

    completed_count = len([x for x in recent if x.outcome == Outcome.completed])
    
    recent_completion_rate = getattr(profile, "recent_completion_rate", 80)
    is_consistent = recent_completion_rate >= 80 and completed_count >= 2 and consecutive_successes >= 2
    has_limited_time = profile.available_minutes <= 15

    topic_struggle_count = {}
    topic_success_count = {}
    for h in recent:
        struggled = h.outcome != Outcome.completed or h.feeling == Feeling.difficult
        if struggled:
            topic_struggle_count[h.topic] = topic_struggle_count.get(h.topic, 0) + 1
        else:
            topic_success_count[h.topic] = topic_success_count.get(h.topic, 0) + 1

    total_explain_requests = getattr(profile, "explanation_requests", 0)
    support_mode_active = total_explain_requests > 0

    needs_revision = (
        len(getattr(profile, "repeated_mistakes", [])) > 0 or
        any(n >= 2 for n in topic_struggle_count.values())
    )

    return LearningState(
        needsRevision=needs_revision,
        shortSuccess=short_success,
        longStruggle=long_struggle,
        consecutiveStruggles=consecutive_struggles,
        consecutiveSuccesses=consecutive_successes,
        isConsistent=is_consistent,
        hasLimitedTime=has_limited_time,
        topicStruggleCount=topic_struggle_count,
        topicSuccessCount=topic_success_count,
        totalExplainRequests=total_explain_requests,
        supportModeActive=support_mode_active
    )

def recommend_difficulty(profile, history, state=None) -> Difficulty:
    s = state if state else analyze_learning_state(profile, history)
    
    if s.needsRevision: return Difficulty.Easy

    current_difficulty = profile.current_difficulty
    if s.consecutiveStruggles >= 3: return prev_difficulty(prev_difficulty(current_difficulty))
    if s.consecutiveStruggles >= 2: return prev_difficulty(current_difficulty)

    if s.isConsistent and s.consecutiveSuccesses >= 3:
        return next_difficulty(next_difficulty(current_difficulty))
    if s.isConsistent: return next_difficulty(current_difficulty)

    return current_difficulty

def calculate_task_priority(activity, profile, history, state: LearningState) -> int:
    score = getattr(activity, "priority", 0)

    revision_topics = getattr(profile, "revision_topics", [])
    topic_name = getattr(activity, "topic", getattr(activity, "topic_name", getattr(activity, "title", "")))

    if topic_name in revision_topics: score += 20
    
    repeated_mistakes = getattr(profile, "repeated_mistakes", [])
    if topic_name in repeated_mistakes: score += 28

    topic_struggles = state.topicStruggleCount.get(topic_name, 0)
    if topic_struggles >= 1: score += topic_struggles * 10

    clamped_duration = min(activity.duration, 25, profile.typical_successful_minutes + 10)
    if clamped_duration > profile.available_minutes: score -= 20
    if profile.available_minutes < 5: score -= 40

    if state.longStruggle and activity.duration > 15: score -= 15
    if state.consecutiveStruggles >= 2 and activity.duration > 10: score -= 12

    if activity.format == profile.preferred_format: score += 8
    if state.supportModeActive and activity.format == Format.Visual: score += 6

    if state.needsRevision and activity.kind == ActivityKind.Revision: score += 18
    if not state.needsRevision and activity.kind == ActivityKind.Revision: score -= 8

    target_diff = recommend_difficulty(profile, history, state)
    if activity.difficulty == target_diff: score += 10
    elif abs(difficulty_value[activity.difficulty] - difficulty_value[target_diff]) == 1:
        score += 3
    else: score -= 15

    return score

def recommend_task_size(profile, history, state: LearningState) -> int:
    base = profile.typical_successful_minutes

    if state.consecutiveStruggles >= 3: return max(5, base - 10)
    if state.consecutiveStruggles >= 2: return max(5, base - 5)
    if state.longStruggle and state.consecutiveStruggles >= 1: return 10

    if state.consecutiveSuccesses >= 4: return min(30, base + 10)
    if state.consecutiveSuccesses >= 2: return min(25, base + 5)

    if state.isConsistent: return min(20, base + 5)
    if state.hasLimitedTime: return min(10, base)

    return base

def recommend_session_duration(profile, history, state: LearningState) -> int:
    size = recommend_task_size(profile, history, state)
    clamped = min(size, profile.available_minutes)
    return max(5, clamped)

def recommend_learning_format(profile, state: LearningState) -> Format:
    if state.totalExplainRequests >= 3: return Format.Visual
    if state.supportModeActive and profile.preferred_format != Format.Visual: return Format.Visual
    return profile.preferred_format

def determine_break(duration: int, profile, state: LearningState) -> int:
    if state.consecutiveStruggles >= 2: return 5
    if duration >= 20 or getattr(profile, "long_activity_abandoned", False): return 4
    if duration >= 15: return 3
    return 2

def determine_support_needed(profile, activity, state: LearningState) -> bool:
    topic_name = getattr(activity, "topic", getattr(activity, "topic_name", getattr(activity, "title", "")))
    return (
        state.supportModeActive or
        topic_name in getattr(profile, "repeated_mistakes", []) or
        state.topicStruggleCount.get(topic_name, 0) >= 1
    )

def select_next_activity(activities, profile, history, state: LearningState):
    if not activities: return None
    scored = []
    for a in activities:
        s = calculate_task_priority(a, profile, history, state)
        scored.append((s, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]

def generate_recommendation_reason(profile, activity, candidate_difficulty, duration, difficulty, support, state: LearningState):
    bullets = []
    adapted_flags = []

    override_up = difficulty_value[difficulty] > difficulty_value[candidate_difficulty]
    override_down = difficulty_value[difficulty] < difficulty_value[candidate_difficulty]
    difficulty_changed_up = difficulty_value[difficulty] > difficulty_value[profile.current_difficulty] or override_up
    difficulty_changed_down = difficulty_value[difficulty] < difficulty_value[profile.current_difficulty] or override_down

    topic_name = getattr(activity, 'topic', getattr(activity, 'topic_name', getattr(activity, 'title', '')))

    if topic_name in getattr(profile, "repeated_mistakes", []):
        bullets.append(f"You have recently found {topic_name.lower()} challenging — this focuses on a topic flagged for review")
        adapted_flags.append("REVISION FOCUS")

    struggles = state.topicStruggleCount.get(topic_name, 0)
    if struggles >= 2:
        bullets.append(f"{topic_name} has been difficult in the last {struggles} sessions — building back confidence with a guided step")
    elif struggles == 1 and topic_name not in getattr(profile, "repeated_mistakes", []):
        bullets.append(f"{topic_name} was tricky last session — consolidating before moving on")

    long_activity_abandoned = getattr(profile, "long_activity_abandoned", False)
    if long_activity_abandoned or state.longStruggle:
        bullets.append("Shorter activities have been more manageable than longer ones — keeping this focused")
        adapted_flags.append("SHORT & FOCUSED")

    if state.consecutiveStruggles >= 2:
        bullets.append(f"After {state.consecutiveStruggles} tricky sessions in a row, this step is intentionally smaller")
        adapted_flags.append("REDUCED TASK SIZE")

    if state.consecutiveSuccesses >= 2 and not state.needsRevision:
        bullets.append(f"{state.consecutiveSuccesses} successful sessions in a row — gently stretching you")
        adapted_flags.append("GENTLE STRETCH")

    if override_up:
        bullets.append(f"This activity has been stepped up to {difficulty.value.lower()} based on your consistent progress")
        adapted_flags.append(f"BOOSTED ↑ {difficulty.value.upper()}")
    elif override_down:
        bullets.append(f"Scaffolded down to {difficulty.value.lower()} so you can rebuild confidence before advancing")
        adapted_flags.append(f"SCAFFOLDED ↓ {difficulty.value.upper()}")
    elif difficulty_changed_up:
        bullets.append(f"Consistent completion lets us try a harder {difficulty.value.lower()} level")
        adapted_flags.append(f"DIFFICULTY: ↑ {difficulty.value.upper()}")
    elif difficulty_changed_down:
        bullets.append(f"Taking difficulty back down to {difficulty.value.lower()} to rebuild confidence")
        adapted_flags.append(f"DIFFICULTY: ↓ {difficulty.value.upper()}")
    else:
        bullets.append(f"Staying at {difficulty.value.lower()} — a good fit right now")

    if activity.format == profile.preferred_format:
        bullets.append(f"Uses your preferred {activity.format.value.lower()} format")
    elif activity.format == Format.Visual and state.totalExplainRequests >= 2:
        bullets.append("Visual format selected because you've asked for extra explanation recently")
        adapted_flags.append("VISUAL SUPPORT")

    bullets.append(f"It fits your {profile.available_minutes} minutes available (this activity: {duration} min)")

    if support:
        bullets.append("An optional simple explanation via Study Buddy is ready if you need it")
        adapted_flags.append("STUDY BUDDY READY")

    if duration <= 10: adapted_flags.append(f"QUICK {duration}MIN STEP")
    if duration >= 20: adapted_flags.append(f"{duration}MIN DEEP DIVE")

    summary_parts = bullets[:2]
    summary = "Recommended because " + "; and ".join(summary_parts) + "."

    return {"summary": summary, "bullets": bullets, "adaptedFlags": adapted_flags}

def generate_recommendation(activities, profile, history):
    state = analyze_learning_state(profile, history)

    desired_difficulty = recommend_difficulty(profile, history, state)
    preferred_format = recommend_learning_format(profile, state)
    duration = recommend_session_duration(profile, history, state)

    candidate = select_next_activity(activities, profile, history, state)
    if not candidate: return None

    topic_name = getattr(candidate, "topic", getattr(candidate, "topic_name", getattr(candidate, "title", "")))
    in_revision = (
        topic_name in getattr(profile, "repeated_mistakes", []) or
        state.topicStruggleCount.get(topic_name, 0) >= 2
    )

    final_difficulty = Difficulty.Easy if in_revision else desired_difficulty
    final_kind = ActivityKind.Revision if in_revision else candidate.kind

    candidate_duration = getattr(candidate, "duration", duration)
    clamped_activity_duration = max(0, min(candidate_duration, duration, profile.available_minutes))

    class LocalActivity: pass
    activity = LocalActivity()
    for k, v in candidate.__dict__.items():
        if not k.startswith("_"): setattr(activity, k, v)
    
    activity.topic = topic_name
    activity.duration = clamped_activity_duration
    activity.difficulty = final_difficulty
    activity.format = preferred_format
    activity.kind = final_kind

    support = determine_support_needed(profile, activity, state)
    break_minutes = determine_break(activity.duration, profile, state)
    score = calculate_task_priority(activity, profile, history, state)
    
    reasoning = generate_recommendation_reason(
        profile,
        activity,
        candidate.difficulty,
        activity.duration,
        final_difficulty,
        support,
        state
    )

    
    return {
        "activity": activity,
        "duration": activity.duration,
        "difficulty": activity.difficulty,
        "format": activity.format,
        "kind": activity.kind,
        "breakMinutes": break_minutes,
        "supportNeeded": support,
        "score": score,
        "reasons": [reasoning["summary"]],
        "bullets": reasoning["bullets"],
        "flags": reasoning["adaptedFlags"],
    }

def update_learning_profile(profile, activity, outcome: Outcome, feeling: Feeling, history: List[Any]):
    success = (outcome == Outcome.completed and feeling != Feeling.difficult)
    struggle = (outcome == Outcome.skipped or outcome == Outcome.partial or feeling == Feeling.difficult)

    completion_weight = 0.75
    new_outcome_score = 100 if outcome == Outcome.completed else (50 if outcome == Outcome.partial else 0)
    completion = round(profile.recent_completion_rate * completion_weight + new_outcome_score * (1 - completion_weight))

    topic_struggles = sum(1 for h in history if h.topic == activity.topic and (h.outcome != Outcome.completed or h.feeling == Feeling.difficult))
    topic_successes = sum(1 for h in history if h.topic == activity.topic and h.outcome == Outcome.completed and h.feeling != Feeling.difficult)

    repeated_mistakes = list(profile.repeated_mistakes)
    if struggle and topic_struggles >= 2:
        if activity.topic not in repeated_mistakes:
            repeated_mistakes.append(activity.topic)
    elif success and activity.topic in repeated_mistakes:
        repeated_mistakes.remove(activity.topic)

    revision_topics = list(profile.revision_topics)
    if struggle and topic_struggles >= 2:
        if activity.topic not in revision_topics:
            revision_topics.append(activity.topic)
    elif success and topic_successes >= 2 and activity.topic in revision_topics:
        revision_topics.remove(activity.topic)

    consecutive_struggles = 0
    for h in reversed(history):
        if h.outcome != Outcome.completed or h.feeling == Feeling.difficult:
            consecutive_struggles += 1
        else:
            break

    consecutive_successes = 0
    for h in reversed(history):
        if h.outcome == Outcome.completed and h.feeling != Feeling.difficult:
            consecutive_successes += 1
        else:
            break

    typical_successful_minutes = profile.typical_successful_minutes
    if success and consecutive_successes >= 2 and activity.duration >= typical_successful_minutes:
        typical_successful_minutes = min(25, typical_successful_minutes + 5)
    elif struggle and consecutive_struggles >= 2 and activity.duration >= typical_successful_minutes:
        typical_successful_minutes = max(5, typical_successful_minutes - 5)

    current_difficulty = profile.current_difficulty
    if success and consecutive_successes % 3 == 0 and completion >= 82:
        if current_difficulty == Difficulty.Easy:
            current_difficulty = Difficulty.Intermediate
        elif current_difficulty == Difficulty.Intermediate:
            current_difficulty = Difficulty.Challenging
    
    if struggle and consecutive_struggles >= 2 and consecutive_struggles % 2 == 0:
        if current_difficulty == Difficulty.Challenging:
            current_difficulty = Difficulty.Intermediate
        elif current_difficulty == Difficulty.Intermediate:
            current_difficulty = Difficulty.Easy

    long_activity_abandoned = profile.long_activity_abandoned
    if activity.duration > 15 and outcome != Outcome.completed:
        long_activity_abandoned = True
    elif success and consecutive_successes >= 2:
        long_activity_abandoned = False

    time_used = activity.duration
    available_minutes = max(0, profile.available_minutes - time_used)
    
    completed_today = profile.completed_today + (1 if outcome == Outcome.completed else 0)

    # We return a new instance or update the existing
    updated = type(profile).__new__(type(profile))
    # copy everything
    for k, v in profile.__dict__.items():
        setattr(updated, k, v)
        
    updated.recent_completion_rate = completion
    updated.completed_today = completed_today
    updated.typical_successful_minutes = typical_successful_minutes
    updated.current_difficulty = current_difficulty
    updated.repeated_mistakes = repeated_mistakes
    updated.revision_topics = revision_topics
    updated.long_activity_abandoned = long_activity_abandoned
    updated.available_minutes = available_minutes
    
    return updated
