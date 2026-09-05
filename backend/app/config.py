import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/learnloop")
ML_ENABLED = os.getenv("ML_ENABLED", "false").lower() == "true"

# Enforce constraints for pilot mode
if APP_ENV == "pilot":
    ML_ENABLED = False  # ML must remain disabled in pilot mode
    if "sqlite" in DATABASE_URL:
        raise ValueError("Pilot mode requires PostgreSQL, but SQLite was detected in DATABASE_URL.")
