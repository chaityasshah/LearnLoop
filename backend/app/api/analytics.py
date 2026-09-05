from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analytics import AnalyticsDashboardResponse
from app.services.analytics_service import get_analytics_dashboard

router = APIRouter()

@router.get("/", response_model=AnalyticsDashboardResponse)
def get_analytics(db: Session = Depends(get_db)):
    """
    Get a high-level analytics dashboard mapping student interactions
    and ML data readiness integrity checks.
    """
    return get_analytics_dashboard(db)
