from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services import supplier_service

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


def _serialize(supplier) -> dict:
    return SupplierRead.model_validate(supplier).model_dump(mode="json")


@router.get("")
def list_suppliers(
    search: str | None = Query(default=None, max_length=100),
    include_inactive: bool = True,
    db: Session = Depends(get_db),
) -> dict:
    """List suppliers (ordered by name), each with a live raw-material count."""
    suppliers = supplier_service.list_suppliers(db, search=search, include_inactive=include_inactive)
    data = {"items": [_serialize(s) for s in suppliers], "count": len(suppliers)}
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)) -> dict:
    supplier = supplier_service.create_supplier(db, payload)
    return {"success": True, "data": _serialize(supplier), "message": "Supplier created."}


@router.get("/{supplier_id}")
def read_supplier(supplier_id: int, db: Session = Depends(get_db)) -> dict:
    supplier = supplier_service.get_supplier_or_404(db, supplier_id)
    return {"success": True, "data": _serialize(supplier)}


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
) -> dict:
    supplier = supplier_service.update_supplier(db, supplier_id, payload)
    return {"success": True, "data": _serialize(supplier), "message": "Supplier updated."}


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)) -> dict:
    supplier_service.delete_supplier(db, supplier_id)
    return {"success": True, "data": None, "message": "Supplier deleted."}
