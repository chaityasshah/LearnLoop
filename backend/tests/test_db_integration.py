import pytest
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import Base
from app.models.student import Student, LearningProfile
from app.db.session import DATABASE_URL

# For this test, we try to use the configured DATABASE_URL.
# If PostgreSQL is not available, it will fail, which is intended.

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(DATABASE_URL)
    try:
        Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        # We don't drop tables here in dev DB
        pass

@pytest.fixture(scope="function")
def db_session(db_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback() # Ensure rollback to clean up state
        session.close()

def test_postgresql_integration(db_session: Session):
    # Setup: Ensure Aarav is not in DB to avoid UniqueViolation
    db_session.execute(text("DELETE FROM learning_profiles WHERE student_id IN (SELECT id FROM students WHERE email='aarav@test.local')"))
    db_session.execute(text("DELETE FROM students WHERE email='aarav@test.local'"))
    db_session.commit()
    
    # 1. Create a student Profile
    student_id = uuid.uuid4()
    new_student = Student(
        id=student_id,
        name="Test Aarav",
        email="aarav@test.local"
    )
    db_session.add(new_student)
    db_session.commit()
    db_session.refresh(new_student)
    
    assert new_student.id is not None
    assert new_student.name == "Test Aarav"
    
    # 2. Create a Learning Profile linked to the Student
    new_profile = LearningProfile(
        student_id=new_student.id,
        preferred_format="Visual",
        typical_successful_minutes=12,
        current_difficulty="Intermediate",
        available_minutes=20,
        long_activity_abandoned=True
    )
    db_session.add(new_profile)
    db_session.commit()
    db_session.refresh(new_profile)
    
    assert new_profile.id is not None
    assert new_profile.student_id == new_student.id
    assert new_profile.current_difficulty == "Intermediate"
    
    # 3. Read back using relationships
    fetched_student = db_session.query(Student).filter(Student.email == "aarav@test.local").first()
    assert fetched_student is not None
    assert fetched_student.profile.preferred_format == "Visual"

