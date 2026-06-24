"""DomOS Cashier MVP - FastAPI Application.

Актуализирано: Премахнати legacy routers за monthly_charges и custom_charges.
Всички задължения се управляват чрез унифицирания /api/obligations endpoint.

Добавено: APScheduler за автоматично генериране на месечни задължения.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import apartments, payments, auth, dashboard, receipts, reports, obligations, expenses
from app.api import scheduler as scheduler_api
from app.scheduler import start_scheduler, stop_scheduler

# Configure logging
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
    
    # Start scheduler
    try:
        start_scheduler()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
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
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
