import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_NAME = "Cafe Management System"
APP_VERSION = "0.1.0"

DATA_DIR = BASE_DIR / "data"
DATABASE_FILE = DATA_DIR / "cafe.db"
DATABASE_URL = os.getenv("CAFE_DATABASE_URL", f"sqlite:///{DATABASE_FILE}")

DEBUG = os.getenv("CAFE_DEBUG", "false").lower() in ("1", "true", "yes")
