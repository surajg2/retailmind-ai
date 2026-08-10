import sys
from pathlib import Path
from alembic.config import Config
from alembic import command

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import settings

def run_migrations():
    print(f"Running Alembic migrations against database: {settings.DATABASE_URL.split('@')[-1]}")
    alembic_cfg = Config(str(BASE_DIR / "backend" / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BASE_DIR / "backend" / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    # Run alembic upgrade head
    command.upgrade(alembic_cfg, "head")
    print("Alembic migrations completed successfully.")

if __name__ == "__main__":
    run_migrations()
