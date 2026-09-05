def test_models_importable():
    try:
        from app.models import Student, LearningProfile, Topic, Activity, LearningEvent, HelpRequest, StateSnapshot
    except ImportError as e:
        assert False, f"Models failed to import: {e}"

def test_schemas_importable():
    try:
        from app.schemas.student import StudentBase
    except ImportError as e:
        assert False, f"Schemas failed to import: {e}"
