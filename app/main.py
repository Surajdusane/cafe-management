from contextlib import asynccontextmanager
from pathlib import Path

import sqlalchemy
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import config
from app.core.database import Base, engine, get_db, init_db
from app.routers.billing import router as billing_router
from app.routers.categories import router as categories_router
from app.routers.inventory import router as inventory_router
from app.routers.menu import router as menu_router
from app.routers.orders import router as orders_router
from app.routers.public_menu import router as public_menu_router
from app.routers.purchases import router as purchases_router
from app.routers.settings import router as settings_router
from app.routers.suppliers import router as suppliers_router

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = BASE_DIR / "static"

PAGES: dict[str, str] = {
    "/": "index.html",
    "/menu": "menu.html",
    "/customer-menu": "customer-menu.html",
    "/orders": "orders.html",
    "/billing": "billing.html",
    "/inventory": "inventory.html",
    "/purchases": "purchases.html",
    "/suppliers": "suppliers.html",
    "/employees": "employees.html",
    "/salaries": "salaries.html",
    "/expenses": "expenses.html",
    "/reports": "reports.html",
    "/settings": "settings.html",
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION, lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(settings_router)
app.include_router(categories_router)
app.include_router(menu_router)
app.include_router(orders_router)
app.include_router(billing_router)
app.include_router(public_menu_router)
app.include_router(suppliers_router)
app.include_router(inventory_router)
app.include_router(purchases_router)


def error_payload(message: str, errors: list | None = None) -> dict:
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return payload


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=error_payload(str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(str(loc) for loc in error.get("loc", []) if loc != "body"),
            "message": error.get("msg", "Invalid value").removeprefix("Value error, "),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content=error_payload("Validation failed", errors))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if config.DEBUG:
        raise exc
    return JSONResponse(status_code=500, content=error_payload("Internal server error"))


@app.get("/api/health")
def health_check(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
        status_code = 200
    except sqlalchemy.SQLAlchemyError:
        database_status = "error"
        status_code = 503
    body = {
        "success": True,
        "data": {
            "status": "ok" if database_status == "connected" else "degraded",
            "app_name": config.APP_NAME,
            "version": config.APP_VERSION,
            "database": database_status,
        },
    }
    return JSONResponse(status_code=status_code, content=body)


@app.get("/api/meta/tables")
def list_tables():
    inspector = sqlalchemy.inspect(engine)
    return {"success": True, "data": {"tables": sorted(inspector.get_table_names())}}


def make_page_handler(filename: str):
    def handler():
        file_path = TEMPLATES_DIR / filename
        if not file_path.exists():
            raise StarletteHTTPException(status_code=404, detail="Page not found")
        return FileResponse(file_path, media_type="text/html")

    return handler


for route, template in PAGES.items():
    app.get(route, include_in_schema=False)(make_page_handler(template))


@app.get("/menu/cafe", include_in_schema=False)
def public_menu_page():
    """Shareable customer-facing digital menu. Kept out of PAGES on purpose:
    it is a public page, not part of the admin navigation."""
    return make_page_handler("public-menu.html")()


def run_server() -> None:
    import os

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("CAFE_HOST", "127.0.0.1"),
        port=int(os.getenv("CAFE_PORT", "8000")),
    )
