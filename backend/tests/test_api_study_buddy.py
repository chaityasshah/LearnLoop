import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_chat_endpoint():
    with patch("app.api.interactions.study_buddy_service.generate_response") as mock_generate:
        mock_generate.return_value = {
            "answer": "Here is how to do it.",
            "sources": []
        }
        
        response = client.post(
            "/api/students/00000000-0000-0000-0000-000000000000/chat",
            json={
                "activity_id": "test_activity",
                "topic": "Fractions",
                "question": "How do I add fractions?",
                "current_difficulty": "Easy",
                "history": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Here is how to do it."
        assert data["sources"] == []
        mock_generate.assert_called_once()
