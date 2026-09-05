import pytest
from unittest.mock import patch, MagicMock
from app.services.study_buddy_service import StudyBuddyService

from langchain_core.runnables import Runnable

class MockChatGroq(Runnable):
    def __init__(self, *args, **kwargs):
        self.called = False
    def invoke(self, *args, **kwargs):
        self.called = True
        from langchain_core.messages import AIMessage
        return AIMessage(content="This is a mocked answer about fractions.")

@pytest.fixture
def mock_study_buddy():
    with patch("app.services.study_buddy_service.ChatGroq", new=MockChatGroq):
        service = StudyBuddyService(api_key="mock_key")
        yield service, service.llm

def test_study_buddy_formatting(mock_study_buddy):
    service, _ = mock_study_buddy
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    formatted = service.format_chat_history(history)
    assert "Human: Hello" in formatted
    assert "Assistant: Hi there!" in formatted

def test_study_buddy_generate_response(mock_study_buddy):
    service, mock_llm = mock_study_buddy
    
    response = service.generate_response(
        question="How do I compare fractions?",
        topic="Fractions",
        difficulty="Intermediate",
        history=[]
    )
    
    assert response["answer"] == "This is a mocked answer about fractions."
    assert response["sources"] == []
    assert mock_llm.called

import tempfile
import os

def test_vectorstore_initialization(mock_study_buddy):
    service, _ = mock_study_buddy
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a mock text document
        test_file_path = os.path.join(tmp_dir, "fractions.txt")
        with open(test_file_path, "w") as f:
            f.write("Equivalent fractions are fractions that represent the same part of a whole.")
            
        service.initialize_vectorstore(tmp_dir)
        
        assert service.vectorstore is not None
        assert service.retriever is not None
        
        # Test retrieval
        response = service.generate_response(
            question="What are equivalent fractions?",
            topic="Fractions",
            difficulty="Easy",
            history=[]
        )
        
        assert response["answer"] == "This is a mocked answer about fractions."
        assert "fractions.txt" in response["sources"]

def test_missing_vectorstore(mock_study_buddy):
    service, _ = mock_study_buddy
    
    # Do not initialize vectorstore, so retriever is None
    service.retriever = None
    response = service.generate_response(
        question="What are equivalent fractions?",
        topic="Fractions",
        difficulty="Easy",
        history=[]
    )
    
    assert response["answer"] == "This is a mocked answer about fractions."
    assert response["sources"] == []

def test_missing_api_key():
    service = StudyBuddyService(api_key="")
    response = service.generate_response(
        question="What are equivalent fractions?",
        topic="Fractions",
        difficulty="Easy",
        history=[]
    )
    assert response["answer"] == "Study Buddy is currently unavailable (API key missing)."
    assert response["sources"] == []
