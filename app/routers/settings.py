from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cafe_setting import CafeSettingRead, CafeSettingUpdate
from app.services import settings_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("")
def read_settings(db: Session = Depends(get_db)) -> dict:
    """Return the cafe settings, creating a default row on first call."""
    settings = settings_service.get_or_create_settings(db)
    data = CafeSettingRead.model_validate(settings).model_dump(mode="json")
    return {"success": True, "data": data}


@router.put("")
def update_settings(payload: CafeSettingUpdate, db: Session = Depends(get_db)) -> dict:
    settings = settings_service.update_settings(db, payload)
    data = CafeSettingRead.model_validate(settings).model_dump(mode="json")
    return {"success": True, "data": data, "message": "Settings saved successfully."}
