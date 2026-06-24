"""API endpoints за управление на Scheduler.

Позволява:
- Преглед на scheduled jobs
- Ръчно тригериране на jobs
- Мониторинг на scheduler статус
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from app.models.user import User
from app.api.auth import get_current_user
from app.scheduler import get_jobs_status, run_job_now, get_scheduler

router = APIRouter()


class JobRunRequest(BaseModel):
    """Request body за ръчно стартиране на job."""
    job_id: str


class JobRunResponse(BaseModel):
    """Response от ръчно стартиране на job."""
    success: bool
    job_id: str
    result: dict | None = None
    error: str | None = None


class SchedulerStatus(BaseModel):
    """Статус на scheduler-а."""
    running: bool
    jobs: list[dict]


@router.get("/status", response_model=SchedulerStatus)
def get_scheduler_status(
    current_user: User = Depends(get_current_user),
):
    """Връща статуса на scheduler-а и списък с jobs."""
    scheduler = get_scheduler()
    
    return SchedulerStatus(
        running=scheduler.running if scheduler else False,
        jobs=get_jobs_status(),
    )


@router.get("/jobs")
def list_jobs(
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Връща списък с всички scheduled jobs."""
    return get_jobs_status()


@router.post("/jobs/run", response_model=JobRunResponse)
async def run_job(
    request: JobRunRequest,
    current_user: User = Depends(get_current_user),
):
    """Ръчно стартира job по ID.
    
    Налични job IDs:
    - generate_monthly_obligations: Генерира месечни задължения за текущия месец
    """
    # Проверка за admin права (опционално - може да се добави)
    # if current_user.role != 'admin':
    #     raise HTTPException(status_code=403, detail="Само администратори могат да стартират jobs")
    
    result = await run_job_now(request.job_id)
    
    return JobRunResponse(
        success=result.get("success", False),
        job_id=request.job_id,
        result=result.get("result"),
        error=result.get("error"),
    )


@router.post("/jobs/generate-monthly")
async def trigger_monthly_obligations(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Shortcut endpoint за генериране на месечни задължения.
    
    Удобен endpoint за касиера да тригерира генериране на месечни задължения
    без да знае job ID.
    """
    result = await run_job_now("generate_monthly_obligations")
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Неуспешно генериране на задължения")
        )
    
    return result.get("result", {})
