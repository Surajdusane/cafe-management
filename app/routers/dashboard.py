from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    """Live dashboard numbers: today's stats, a 7-day sales trend, top sellers
    and recent orders — all recomputed from recorded data."""
    data = dashboard_service.dashboard_summary(db)
    return {"success": True, "data": data}