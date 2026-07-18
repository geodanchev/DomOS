"""Database session management.

Cloud Run Compatibility:
- Supports Cloud SQL Unix socket connections
- Configurable connection pooling for serverless environments
- Connection health checks and recycling
- Lazy initialization to prevent startup failures
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional
import logging

logger = logging.getLogger(__name__)

# Lazy-initialized engine and session factory
_engine = None
_SessionLocal = None


def _get_settings():
    """Get settings lazily to avoid import-time failures."""
    from app.core.config import settings
    return settings


def get_engine():
    """Create database engine with appropriate settings.
    
    Cloud Run considerations:
    - Use connection pooling with limits suitable for serverless
    - Enable pool pre-ping for connection health checks
    - Set pool recycle to handle Cloud SQL connection timeouts
    """
    global _engine
    if _engine is not None:
        return _engine
    
    settings = _get_settings()
    
    logger.info(f"Creating database engine...")
    logger.info(f"Database URL prefix: {settings.DATABASE_URL[:30]}..." if len(settings.DATABASE_URL) > 30 else f"Database URL: {settings.DATABASE_URL}")
    logger.info(f"Cloud Run mode: {settings.is_cloud_run}")
    
    engine_args = {
        "pool_pre_ping": True,  # Verify connections before use
        "echo": settings.DEBUG,  # SQL logging in debug mode
    }
    
    # Configure connection pool for Cloud Run
    if settings.is_cloud_run:
        # Cloud Run: Use conservative pool settings
        # Each instance may handle multiple concurrent requests
        engine_args.update({
            "poolclass": QueuePool,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        })
    else:
        # Local development: simpler settings
        engine_args.update({
            "pool_size": 5,
            "max_overflow": 10,
        })
    
    try:
        _engine = create_engine(settings.DATABASE_URL, **engine_args)
        logger.info("Database engine created successfully")
        return _engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def get_session_local():
    """Get or create the session factory lazily."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


# Legacy exports for backwards compatibility
# These are now properties that lazily initialize
class _LazyEngine:
    """Lazy proxy for the database engine."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)
    
    def __bool__(self):
        return _engine is not None or True  # Always truthy for health checks


class _LazySessionLocal:
    """Lazy proxy for SessionLocal."""
    def __call__(self):
        return get_session_local()()
    
    def __getattr__(self, name):
        return getattr(get_session_local(), name)


# Export lazy proxies
engine = _LazyEngine()
SessionLocal = _LazySessionLocal()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
