from enum import Enum

class Format(str, Enum):
    Visual = "Visual"
    Text = "Text"
    AudioReady = "Audio-ready"

class Difficulty(str, Enum):
    Easy = "Easy"
    Intermediate = "Intermediate"
    Challenging = "Challenging"

class ActivityKind(str, Enum):
    Practice = "Practice"
    Revision = "Revision"
    Learn = "Learn"

class Outcome(str, Enum):
    completed = "completed"
    partial = "partial"
    skipped = "skipped"

class Feeling(str, Enum):
    easy = "easy"
    manageable = "manageable"
    difficult = "difficult"
