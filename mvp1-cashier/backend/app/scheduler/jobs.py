"""Дефиниции на scheduled jobs.

Този модул съдържа функциите, които се изпълняват от scheduler-а.
Всяка функция трябва да бъде async и да обработва собствените си exceptions.
"""

import logging
from datetime import datetime, date
from typing import Any

from app.db.session import SessionLocal
from app.services.obligation_service import ObligationService

logger = logging.getLogger(__name__)


async def generate_monthly_obligations_job() -> dict[str, Any]:
    """Job за автоматично генериране на месечни задължения.
    
    Тази функция се изпълнява автоматично на 1-во число от всеки месец.
    Генерира месечни задължения за всички апартаменти за текущия месец.
    
    Returns:
        dict с резултат от операцията:
        - success: bool
        - month: str (YYYY-MM)
        - created_count: int (брой създадени задължения)
        - skipped_count: int (брой пропуснати - вече съществуващи)
        - errors: list[str] (евентуални грешки)
    """
    # Определи текущия месец
    today = date.today()
    current_month = today.strftime("%Y-%m")
    
    logger.info(f"Starting monthly obligations generation for {current_month}")
    
    result = {
        "success": False,
        "month": current_month,
        "created_count": 0,
        "skipped_count": 0,
        "errors": [],
        "executed_at": datetime.now().isoformat(),
    }
    
    db = None
    try:
        # Създай database session
        db = SessionLocal()
        service = ObligationService(db)
        
        # Генерирай месечни задължения
        # Тази функция в service-а вече проверява за дубликати
        created_obligations = service.generate_monthly_obligations(current_month)
        
        result["success"] = True
        result["created_count"] = len(created_obligations)
        
        logger.info(
            f"Monthly obligations generation completed: "
            f"{len(created_obligations)} obligations created for {current_month}"
        )
        
        # Log детайли за създадените задължения
        for obligation in created_obligations:
            logger.debug(
                f"Created obligation: apt={obligation.apartment_id}, "
                f"amount={obligation.amount}, month={obligation.month}"
            )
        
    except Exception as e:
        error_msg = f"Error generating monthly obligations: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result["errors"].append(error_msg)
        
        # При грешка се опитай да rollback-неш
        if db:
            try:
                db.rollback()
            except Exception:
                pass
    
    finally:
        # Затвори database session
        if db:
            try:
                db.close()
            except Exception:
                pass
    
    return result


async def cleanup_old_logs_job() -> dict[str, Any]:
    """Job за почистване на стари логове (placeholder за бъдеща имплементация).
    
    Може да се използва за:
    - Архивиране на стари audit logs
    - Почистване на temporary данни
    - Maintenance операции
    """
    logger.info("Cleanup job executed (placeholder)")
    return {
        "success": True,
        "message": "Cleanup job placeholder - no action taken",
        "executed_at": datetime.now().isoformat(),
    }
