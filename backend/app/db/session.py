import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy engine - only connect when actually needed
_engine = None
_SessionLocal = None
_last_db_check = 0.0
_is_db_online = False

def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            settings.get_database_url,
            pool_pre_ping=False,
            connect_args={"connect_timeout": 1},
            pool_size=1,
            max_overflow=0
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine, _SessionLocal

def is_db_connected(force_check: bool = False) -> bool:
    global _last_db_check, _is_db_online
    now = time.time()
    if not force_check and (now - _last_db_check) < 10.0:
        return _is_db_online

    _last_db_check = now
    try:
        engine, _ = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _is_db_online = True
    except Exception:
        _is_db_online = False
    return _is_db_online

def SessionLocal():
    """Returns a new session."""
    _, sl = get_engine()
    return sl()

