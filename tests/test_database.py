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


def test_metadata_has_no_domain_tables_yet():
    domain_tables = {
        "categories",
        "menu_items",
        "orders",
        "order_items",
        "inventory_items",
        "suppliers",
        "purchases",
        "employees",
        "salaries",
        "expenses",
    }

    assert not domain_tables.intersection(Base.metadata.tables.keys())
