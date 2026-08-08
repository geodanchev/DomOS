"""Cloud Scheduler Cron Endpoints.

Тези endpoints са предназначени за извикване от Google Cloud Scheduler.
Използват OIDC token authentication вместо JWT.

SECURITY:
- Валидира се, че заявката идва от оторизиран service account
- Поддържа се и CRON_SECRET header за допълнителна защита
- Логват се всички извиквания
"""

import logging
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Header, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.db.session import SessionLocal
from app.services.obligation_service import ObligationService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed service account patterns for Cloud Scheduler
# Any service account from the same GCP project is allowed
ALLOWED_SA_DOMAINS = [
    f"@{settings.GCP_PROJECT_ID}.iam.gserviceaccount.com",
    "@developer.gserviceaccount.com",  # Default compute SA
    "@cloudbuild.gserviceaccount.com",  # Cloud Build SA
]

# Specific allowed service accounts (if needed)
ALLOWED_SERVICE_ACCOUNTS = [
    f"cloud-scheduler-invoker@{settings.GCP_PROJECT_ID}.iam.gserviceaccount.com",
    f"{settings.GCP_PROJECT_NUMBER}-compute@developer.gserviceaccount.com",
]

# Optional: Secret key for additional validation
CRON_SECRET = os.getenv("CRON_SECRET", "")


async def verify_cloud_scheduler_request(
    request: Request,
    authorization: str | None = Header(None),
    x_cron_secret: str | None = Header(None, alias="X-Cron-Secret"),
) -> dict[str, Any]:
    """Верифицира, че заявката идва от Cloud Scheduler.
    
    Проверява:
    1. OIDC token в Authorization header (от Cloud Scheduler)
    2. Опционално: X-Cron-Secret header за допълнителна защита
    
    Returns:
        dict с информация за верифицирания caller
    
    Raises:
        HTTPException 401/403 при невалидна автентикация
    """
    caller_info = {
        "verified": False,
        "method": None,
        "email": None,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Метод 1: Проверка на OIDC token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            # Верифицирай OIDC token от Google
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                audience=settings.BACKEND_URL,  # Cloud Run URL
            )
            
            email = idinfo.get("email", "")
            caller_info["email"] = email
            
            # Провери дали email е в списъка с позволени service accounts или domains
            is_allowed = (
                email in ALLOWED_SERVICE_ACCOUNTS or
                any(email.endswith(domain) for domain in ALLOWED_SA_DOMAINS)
            )
            
            if is_allowed:
                caller_info["verified"] = True
                caller_info["method"] = "oidc_token"
                logger.info(f"Cloud Scheduler request verified via OIDC: {email}")
            else:
                logger.warning(f"OIDC token from unauthorized account: {email}")
                
        except Exception as e:
            logger.warning(f"OIDC token verification failed: {e}")
    
    # Метод 2: Проверка на CRON_SECRET (fallback за development)
    if not caller_info["verified"] and CRON_SECRET:
        if x_cron_secret == CRON_SECRET:
            caller_info["verified"] = True
            caller_info["method"] = "cron_secret"
            caller_info["email"] = "cron_secret_auth"
            logger.info("Cloud Scheduler request verified via CRON_SECRET")
    
    # Ако нито един метод не е успял
    if not caller_info["verified"]:
        logger.error(f"Unauthorized cron request from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing Cloud Scheduler authentication",
        )
    
    return caller_info


@router.post("/generate-monthly-obligations")
async def generate_monthly_obligations_cron(
    request: Request,
    authorization: str | None = Header(None),
    x_cron_secret: str | None = Header(None, alias="X-Cron-Secret"),
) -> dict[str, Any]:
    """Cloud Scheduler endpoint за генериране на месечни задължения.
    
    Този endpoint се извиква автоматично от Cloud Scheduler на 1-во число.
    
    Authentication:
    - OIDC token от Cloud Scheduler service account
    - Или X-Cron-Secret header (за development/testing)
    
    Returns:
        dict с резултат от операцията
    """
    # Верифицирай заявката
    caller_info = await verify_cloud_scheduler_request(
        request, authorization, x_cron_secret
    )
    
    # Изпълни генерирането на задължения
    from datetime import date
    current_month = date.today().strftime("%Y-%m")
    
    logger.info(f"Starting monthly obligations generation for {current_month} via Cloud Scheduler")
    
    result = {
        "success": False,
        "month": current_month,
        "created_count": 0,
        "skipped_count": 0,
        "errors": [],
        "executed_at": datetime.now().isoformat(),
        "triggered_by": caller_info["email"],
        "auth_method": caller_info["method"],
    }
    
    db = None
    try:
        db = SessionLocal()
        service = ObligationService(db)
        
        # Генерирай месечни задължения
        created_obligations = service.generate_monthly_obligations(current_month)
        
        result["success"] = True
        result["created_count"] = len(created_obligations)
        
        logger.info(
            f"Monthly obligations generation completed: "
            f"{len(created_obligations)} obligations created for {current_month}"
        )
        
    except Exception as e:
        error_msg = f"Error generating monthly obligations: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result["errors"].append(error_msg)
        
        if db:
            try:
                db.rollback()
            except Exception:
                pass
    
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result,
        )
    
    return result


@router.get("/health")
async def cron_health() -> dict[str, str]:
    """Health check endpoint за Cloud Scheduler.
    
    Може да се използва от Cloud Scheduler за проверка дали endpoint-ът е достъпен.
    """
    return {
        "status": "healthy",
        "service": "cron",
        "timestamp": datetime.now().isoformat(),
    }
