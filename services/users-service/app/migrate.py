"""Runs Alembic migrations programmatically so the schema upgrades itself
whenever the service starts — no separate migration step to remember, and
existing rows are never dropped the way `Base.metadata.create_all()` +
manual `ALTER TABLE`s would be if a column changes.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

_SERVICE_ROOT = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    cfg = Config(str(_SERVICE_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_SERVICE_ROOT / "migrations"))
    return cfg


def upgrade_to_head() -> None:
    """Synchronous by nature (Alembic's own API); call via `asyncio.to_thread`
    from async startup code so it doesn't block the event loop."""
    command.upgrade(_alembic_config(), "head")
