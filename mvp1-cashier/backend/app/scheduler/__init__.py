"""APScheduler модул за автоматизирани задачи.

Основни функции:
- Автоматично генериране на месечни задължения на 1-во число
- Управление на scheduler lifecycle
- API за ръчно тригериране на jobs
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from app.scheduler.jobs import generate_monthly_obligations_job

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


def job_listener(event):
    """Listener за logging на job events."""
    if event.exception:
        logger.error(
            f"Job {event.job_id} failed with exception: {event.exception}",
            exc_info=True
        )
    else:
        logger.info(
            f"Job {event.job_id} executed successfully at {datetime.now()}"
        )


def create_scheduler() -> AsyncIOScheduler:
    """Създава и конфигурира scheduler instance."""
    global scheduler
    
    scheduler = AsyncIOScheduler(
        timezone="Europe/Sofia",
        job_defaults={
            'coalesce': True,  # Комбинира пропуснати изпълнения в едно
            'max_instances': 1,  # Само една инстанция на job в даден момент
            'misfire_grace_time': 3600,  # 1 час grace time за пропуснати jobs
        }
    )
    
    # Добави listener за logging
    scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
    
    # Регистрирай jobs
    _register_jobs(scheduler)
    
    return scheduler


def _register_jobs(sched: AsyncIOScheduler):
    """Регистрира всички scheduled jobs."""
    
    # Job за генериране на месечни задължения
    # Изпълнява се на 1-во число от всеки месец в 00:05 часа
    sched.add_job(
        generate_monthly_obligations_job,
        trigger=CronTrigger(
            day=1,
            hour=0,
            minute=5,
            timezone="Europe/Sofia"
        ),
        id="generate_monthly_obligations",
        name="Генериране на месечни задължения",
        replace_existing=True,
    )
    
    logger.info("Registered job: generate_monthly_obligations (cron: 0 0 5 1 * *)")


def start_scheduler():
    """Стартира scheduler-а."""
    global scheduler
    
    if scheduler is None:
        scheduler = create_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Log всички регистрирани jobs
        jobs = scheduler.get_jobs()
        for job in jobs:
            logger.info(
                f"Scheduled job: {job.id} - next run: {job.next_run_time}"
            )


def stop_scheduler():
    """Спира scheduler-а."""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def get_scheduler() -> AsyncIOScheduler | None:
    """Връща текущия scheduler instance."""
    return scheduler


def get_jobs_status() -> list[dict]:
    """Връща статуса на всички jobs."""
    if scheduler is None:
        return []
    
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }
        for job in jobs
    ]


async def run_job_now(job_id: str) -> dict:
    """Ръчно изпълнява job веднага."""
    if scheduler is None:
        return {"success": False, "error": "Scheduler not initialized"}
    
    job = scheduler.get_job(job_id)
    if job is None:
        return {"success": False, "error": f"Job '{job_id}' not found"}
    
    try:
        # Изпълни job функцията директно
        if job_id == "generate_monthly_obligations":
            result = await generate_monthly_obligations_job()
            return {"success": True, "result": result}
        else:
            return {"success": False, "error": f"Unknown job: {job_id}"}
    except Exception as e:
        logger.error(f"Error running job {job_id}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
