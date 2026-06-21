"""DomOS Cashier MVP - FastAPI Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import apartments, payments, monthly_charges, auth, dashboard

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Дигитален касиер за етажна собственост",
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
app.include_router(monthly_charges.router, prefix="/api/charges", tags=["Задължения"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Табло"])


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
