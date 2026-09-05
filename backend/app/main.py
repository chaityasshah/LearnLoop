from fastapi import FastAPI
from app.api import students, activities, interactions, analytics, health
from app.db.session import engine
from app.models.base import Base
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from app.config import APP_ENV, ML_ENABLED
    logger.info(f"Starting LearnLoop API in {APP_ENV.upper()} mode (ML_ENABLED={ML_ENABLED})")
    # create_all uses checkfirst=True semantics (it won't drop existing tables)
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.error(f"Could not connect to database to create tables: {e}")

app = FastAPI(title="LearnLoop API")

# CORS: allow local dev origins plus the deployed frontend origin (FRONTEND_ORIGIN env var).
# Always include localhost for local development convenience.
_frontend_origin = os.getenv("FRONTEND_ORIGIN", "")
_allowed_origins = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://localhost:3000",
]
if _frontend_origin:
    _allowed_origins.append(_frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])

app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(interactions.router, prefix="/api/students", tags=["interactions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
