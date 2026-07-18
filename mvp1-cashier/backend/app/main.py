"""DomOS Cashier MVP - FastAPI Application.

Актуализирано: Премахнати legacy routers за monthly_charges и custom_charges.
Всички задължения се управляват чрез унифицирания /api/obligations endpoint.

Добавено: APScheduler за автоматично генериране на месечни задължения.

Cloud Run Compatibility:
- Health check endpoints for liveness and readiness probes
- Configurable PORT from environment
- Structured logging for Cloud Logging
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api import apartments, payments, auth, dashboard, receipts, reports, obligations, expenses
from app.api import scheduler as scheduler_api
from app.scheduler import start_scheduler, stop_scheduler
from app.db.session import SessionLocal, engine

# Configure logging
# Use structured logging format for Cloud Run/Cloud Logging
if settings.is_cloud_run:
    # JSON structured logging for Cloud Logging
    import json
    
    class CloudLoggingFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "severity": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "timestamp": self.formatTime(record),
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLoggingFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager за startup/shutdown events."""
    # Startup
    logger.info("Starting DomOS Cashier application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Cloud Run: {settings.is_cloud_run}")
    
    # Start scheduler (only if not in minimal mode)
    if not settings.is_cloud_run or settings.ENVIRONMENT != "production":
        try:
            start_scheduler()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    else:
        logger.info("Scheduler disabled in Cloud Run production mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DomOS Cashier application...")
    
    # Stop scheduler
    try:
        stop_scheduler()
        logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Дигитален касиер за етажна собственост",
    lifespan=lifespan,
    # Disable docs in production
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Автентикация"])
app.include_router(apartments.router, prefix="/api/apartments", tags=["Апартаменти"])
app.include_router(payments.router, prefix="/api/payments", tags=["Плащания"])
app.include_router(obligations.router, prefix="/api", tags=["Задължения"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Табло"])
app.include_router(receipts.router, tags=["Разписки"])
app.include_router(reports.router, prefix="/api/reports", tags=["Справки"])
app.include_router(scheduler_api.router, prefix="/api/scheduler", tags=["Scheduler"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Разходи"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint.
    
    Returns 200 if the application is running.
    Used for simple health checks.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint for Cloud Run.
    
    Returns 200 if the application process is alive.
    A failure here indicates the container should be restarted.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint for Cloud Run.
    
    Returns 200 if the application is ready to receive traffic.
    Checks database connectivity.
    A failure here indicates the container should not receive traffic.
    """
    # Check database connectivity
    try:
        db = SessionLocal()
        try:
            # Simple query to verify database connection
            db.execute(text("SELECT 1"))
            db_status = "connected"
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        # Return 503 Service Unavailable if database is not ready
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e),
            }
        )
    
    return {
        "status": "ready",
        "database": db_status,
    }


@app.get("/health/startup")
async def startup_check():
    """Startup probe endpoint for Cloud Run.
    
    Returns 200 when the application has completed initialization.
    This allows for longer startup times without failing liveness checks.
    """
    # Check if essential components are initialized
    # Note: engine and settings use lazy initialization, so we just check they're importable
    checks = {
        "app_initialized": True,
        "settings_loaded": settings is not None,
    }
    
    return {
        "status": "started",
        "checks": checks,
    }
