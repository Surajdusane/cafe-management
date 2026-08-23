from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import public_menu_service

router = APIRouter(prefix="/api/public/menu", tags=["Public Menu"])


@router.get("")
def read_public_menu(db: Session = Depends(get_db)) -> dict:
    """Public digital menu: cafe branding plus active categories and their items.

    This endpoint is safe to share with customers. It exposes no admin fields
    (no ids, timestamps, availability controls or billing configuration).
    """
    data = public_menu_service.get_public_menu(db)
    return {"success": True, "data": data}
