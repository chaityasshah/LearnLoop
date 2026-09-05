import os
from app.db.session import DATABASE_URL, engine

def test_database_url_configured():
    assert DATABASE_URL is not None
    assert "postgresql://" in DATABASE_URL

def test_engine_creation():
    assert engine is not None
