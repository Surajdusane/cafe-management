from sqlalchemy import text

from app.core.config import DATABASE_FILE, DATABASE_URL
from app.core.database import Base, SessionLocal, engine, init_db


def test_database_url_points_to_sqlite_file():
    assert str(engine.url).startswith("sqlite")
    assert "cafe.db" in DATABASE_URL


def test_init_db_creates_database_file():
    engine.dispose()
    if DATABASE_FILE.exists():
        DATABASE_FILE.unlink()

    init_db()

    assert DATABASE_FILE.parent.exists() and DATABASE_FILE.exists()


def test_session_executes_select():
    init_db()

    with SessionLocal() as session:
        result = session.execute(text("SELECT 1")).scalar()

        assert result == 1


def test_metadata_registers_implemented_tables():
    registered = set(Base.metadata.tables.keys())

    assert {
        "cafe_settings",
        "categories",
        "menu_items",
        "orders",
        "order_items",
        "suppliers",
        "inventory_items",
        "inventory_transactions",
        "purchases",
        "purchase_items",
    }.issubset(registered)


def test_metadata_has_no_future_domain_tables_yet():
    future_tables = {
        "employees",
        "salaries",
        "expenses",
    }

    assert not future_tables.intersection(Base.metadata.tables.keys())
