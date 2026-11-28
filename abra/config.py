import os
from pathlib import Path

APP_NAME = "ABRA FINANCES"
VERSION = "4.1"
COMPANY = "SAVVY SOFT"

BASE_DIR = Path.home() / "Documents" / "ABRA"
DB_PATH = BASE_DIR / "data.db"
BACKUP_DIR = BASE_DIR / "backups"
LICENSE_FILE = BASE_DIR / "license.json"

SAVVY_SECRET = os.environ.get("SAVVY_SECRET", "CHANGE-ME-ON-PC")

def ensure_dirs():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
