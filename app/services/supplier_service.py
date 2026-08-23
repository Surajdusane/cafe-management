from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryItem
from app.models.supplier import Supplier


def _raise_duplicate(db: Session, name: str, exclude_id: int | None = None) -> None:
    """Raise 409 when another supplier already uses the same name (case-insensitive)."""
    stmt = select(Supplier).where(func.lower(Supplier.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(Supplier.id != exclude_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'A supplier named "{existing.name}" already exists.',
        )


def _item_count_stmt():
    return (
        select(func.count(InventoryItem.id))
        .where(InventoryItem.supplier_id == Supplier.id)
        .correlate(Supplier)
        .scalar_subquery()
    )


def list_suppliers(
    db: Session,
    search: str | None = None,
    include_inactive: bool = True,
) -> list[Supplier]:
    """Return suppliers ordered by name, each with a live raw-material count."""
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(
            or_(
                Supplier.name.ilike(term),
                Supplier.contact_person.ilike(term),
                Supplier.materials_supplied.ilike(term),
                Supplier.phone.ilike(term),
            )
        )
    if not include_inactive:
        conditions.append(Supplier.is_active.is_(True))

    stmt = select(Supplier, _item_count_stmt().label("inventory_item_count"))
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(Supplier.name)

    suppliers: list[Supplier] = []
    for supplier, count in db.execute(stmt).all():
        supplier.inventory_item_count = count
        suppliers.append(supplier)
    return suppliers


def get_supplier_or_404(db: Session, supplier_id: int) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} was not found.",
        )
    supplier.inventory_item_count = len(supplier.inventory_items)
    return supplier


def validate_supplier_exists(db: Session, supplier_id: int) -> Supplier:
    """Used by the inventory service; a material's supplier must be real."""
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} was not found. Create it first.",
        )
    return supplier


def create_supplier(db: Session, payload) -> Supplier:
    _raise_duplicate(db, payload.name)
    supplier = Supplier(**payload.model_dump())
    supplier.inventory_item_count = 0
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def update_supplier(db: Session, supplier_id: int, payload) -> Supplier:
    supplier = get_supplier_or_404(db, supplier_id)
    _raise_duplicate(db, payload.name, exclude_id=supplier_id)

    for field, value in payload.model_dump().items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)

    supplier.inventory_item_count = len(supplier.inventory_items)
    return supplier


def delete_supplier(db: Session, supplier_id: int) -> None:
    """Delete a supplier. Raw materials keep working: their supplier link is
    cleared automatically (FK ON DELETE SET NULL); nothing else references it."""
    supplier = get_supplier_or_404(db, supplier_id)
    db.delete(supplier)
    db.commit()
