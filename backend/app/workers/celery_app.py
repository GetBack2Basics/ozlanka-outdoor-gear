from datetime import timedelta

from celery import Celery
from celery.schedules import schedule

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "ozlanka",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery.conf.update(
    timezone="UTC",
    task_track_started=True,
    beat_schedule={
        "scrape-every-14-days": {
            "task": "app.workers.tasks.trigger_scrape",
            "schedule": schedule(timedelta(seconds=settings.scrape_interval_seconds)),
        }
    },
)
