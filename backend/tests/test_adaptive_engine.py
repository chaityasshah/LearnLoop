import pytest
import json
import os
from app.services.adaptive_engine import generate_recommendation
from app.schemas.enums import Difficulty, Format, ActivityKind, Outcome, Feeling

class MockObject:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def to_enum(val, enum_cls):
    if not val: return val
    try:
        return enum_cls(val)
    except ValueError:
        return val

def build_activities(acts):
    res = []
    for d in acts:
        res.append(MockObject(
            id=d['id'],
            topic=d['topic'],
            title=d['title'],
            duration=d['duration'],
            difficulty=to_enum(d['difficulty'], Difficulty),
            format=to_enum(d['format'], Format),
            kind=to_enum(d.get('kind', 'Practice'), ActivityKind),
            priority=d.get('priority', 0)
        ))
    return res

def build_profile(p):
    return MockObject(
        student_id=p.get("studentId", "dummy"),
        preferred_format=to_enum(p.get("preferredFormat"), Format),
        typical_successful_minutes=p.get("typicalSuccessfulMinutes"),
        current_difficulty=to_enum(p.get("currentDifficulty"), Difficulty),
        available_minutes=p.get("availableMinutes"),
        recent_completion_rate=p.get("recentCompletionRate"),
        completed_today=p.get("completedToday"),
        repeated_mistakes=p.get("repeatedMistakes", []),
        revision_topics=p.get("revisionTopics", []),
        explanation_requests=p.get("explanationRequests"),
        long_activity_abandoned=p.get("longActivityAbandoned")
    )

def build_history(h_list):
    res = []
    for h in h_list:
        res.append(MockObject(
            id=h.get('id'),
            activity_id=h.get('activityId'),
            topic=h.get('topic'),
            title=h.get('title'),
            recommended_duration=h.get('recommendedDuration'),
            actual_duration=h.get('actualDuration', h.get('duration')),
            difficulty=to_enum(h.get('difficulty'), Difficulty),
            format=to_enum(h.get('format'), Format),
            outcome=to_enum(h.get('outcome'), Outcome),
            feeling=to_enum(h.get('feeling'), Feeling)
        ))
    return res

def load_fixtures():
    path = os.path.join(os.path.dirname(__file__), 'fixtures', 'engine_fixtures.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

@pytest.mark.parametrize("name", load_fixtures().keys())
def test_engine_parity(name):
    fixtures = load_fixtures()
    data = fixtures[name]
    
    inputs = data['inputs']
    expected = data['expected']
    
    activities = build_activities(inputs['activities'])
    profile = build_profile(inputs['profile'])
    history = build_history(inputs['history'])
    
    result = generate_recommendation(activities, profile, history)
    
    # Assertions
    assert result["activity"].id == expected["activity"]["id"], f"{name}: activity id mismatch"
    assert result["duration"] == expected["duration"], f"{name}: duration mismatch"
    assert result["difficulty"].value == expected["difficulty"], f"{name}: difficulty mismatch"
    assert result["format"].value == expected["format"], f"{name}: format mismatch"
    assert result["kind"].value == expected["kind"], f"{name}: kind mismatch"
    assert result["breakMinutes"] == expected["breakMinutes"], f"{name}: breakMinutes mismatch"
    assert result["supportNeeded"] == expected["supportNeeded"], f"{name}: supportNeeded mismatch"
    assert result["score"] == expected["score"], f"{name}: score mismatch"
    
    assert set(result["flags"]) == set(expected["flags"]), f"{name}: flags mismatch. Got {result['flags']} expected {expected['flags']}"
    assert set(result["bullets"]) == set(expected["bullets"]), f"{name}: bullets mismatch. Got {result['bullets']} expected {expected['bullets']}"
    assert result["reasons"] == expected["reasons"], f"{name}: reasons mismatch. Got {result['reasons']} expected {expected['reasons']}"
