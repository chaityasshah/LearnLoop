# Future ML Architecture

This document outlines the proposed design for integrating a Machine Learning (ML) model into the LearnLoop Adaptive Decision Engine, ensuring it remains safe, interpretable, and highly effective.

## Pipeline Architecture

The system will transition from a purely heuristic engine to a **Candidate Filtering -> ML Ranking -> Deterministic Constraint** pipeline.

```text
Student State + Activity Features
             ↓
       Candidate Filter (Deterministic)
             ↓
       ML Success Score
             ↓
Deterministic Safety Constraints
             ↓
    Final Recommendation
```

### 1. Candidate Filter (Deterministic)
Before any ML prediction, the engine will filter out activities that are strictly invalid:
- Topics that have already been mastered and do not require revision.
- Activities exceeding the student's strictly `available_minutes`.
- Difficulties fundamentally mismatched with the student's current level (e.g., preventing 'Challenging' if they are consistently struggling with 'Easy').

### 2. ML Success Score (Predictive Model)
For the remaining valid activities, an ML Model (e.g., XGBoost or a lightweight Neural Network) will predict:
`P(success | student_state, activity_features)`

The model will ingest features exported by `export_training_data.py`:
- `recent_completion_rate`
- `topic_success_rate`
- `recent_struggle_count`
- `help_request_frequency`
- `time_since_last_seen_hours`
- Activity metadata (`duration`, `format`, `difficulty`)

**Target**: The probability that the student will complete the activity without abandoning it or flagging it as too difficult.

### 3. Deterministic Safety Constraints
After the ML model ranks the activities by predicted success probability, a final deterministic layer applies pedagogical constraints:
- **Format Match**: Boost activities that match the `preferred_format`.
- **Revision Urgency**: Override the ML score if a topic is explicitly flagged for urgent revision.
- **Fatigue Protection**: If `completed_today` is very high, forcefully select the shortest possible activity regardless of ML score, or recommend a break.

## Why Not a Black Box?
By restricting the ML model to *scoring valid candidates* rather than *generating recommendations directly*, we guarantee that the system will never recommend a 45-minute activity to a student who only has 5 minutes left, no matter what the model learns. The Deterministic Engine remains the final safety arbiter.
